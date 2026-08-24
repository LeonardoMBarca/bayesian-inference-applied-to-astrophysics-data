"""Conservative public-data collector for ETD / VarAstro."""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests

from .utils import (
    RawDataManifest,
    atomic_write_text,
    csv_bytes,
    register_error,
    safe_slug,
    save_artifact,
    sha256_file,
    utc_now,
    versioned_path,
)

SOURCE_NAME = "ETD / VarAstro"
OBSERVATION_COLUMNS = (
    "planet",
    "epoch",
    "mid_transit_time",
    "duration",
    "depth",
    "quality",
    "filter",
    "observer",
    "light_curve_url",
    "source_url",
    "table_index",
    "row_index",
    "raw_metadata_json",
)
ETD_MANIFEST_COLUMNS = (
    "collected_at_utc",
    "planet_name",
    "host_star",
    "source_url",
    "local_path",
    "file_type",
    "product_type",
    "status",
    "error_message",
    "sha256",
    "file_size_bytes",
    "notes",
)
FILE_EXTENSIONS = {".csv", ".txt", ".dat", ".tsv", ".lc", ".fit", ".fits"}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _sleep(config: Any) -> None:
    time.sleep(config.ETD_REQUEST_DELAY_SECONDS)


def _is_public_varastro_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower() in {
        "var.astro.cz",
        "www.var.astro.cz",
    }


def _get(
    session: requests.Session,
    config: Any,
    url: str,
    *,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    _sleep(config)
    response = session.get(
        url,
        params=params,
        headers=headers,
        timeout=config.REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response


def _save_html(
    response: requests.Response,
    path: Path,
    manifest: RawDataManifest,
    *,
    planet_name: str,
    host_star: str,
    product_type: str,
    search_term: str,
) -> bool:
    return save_artifact(
        manifest,
        path,
        response.content,
        source_name=SOURCE_NAME,
        source_url=response.url,
        planet_name=planet_name,
        host_star=host_star,
        file_type="html",
        product_type=product_type,
        query_or_search_term=search_term,
        notes="Unmodified public HTML response from VarAstro.",
    )


def _find_planet_detail_url(soup: Any, base_url: str, planet_name: str) -> str | None:
    target = _normalize(planet_name)
    host_target = _normalize(planet_name.removesuffix(" b"))
    candidates: list[tuple[int, str]] = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor["href"])
        if not _is_public_varastro_url(href):
            continue
        text = " ".join(anchor.stripped_strings)
        combined = _normalize(f"{text} {unquote(href)}")
        score = 0
        if target and target in combined:
            score += 5
        if host_target and host_target in combined:
            score += 2
        if "exoplanet" in href.lower():
            score += 1
        if score:
            candidates.append((score, href))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _field_value(raw_row: dict[str, str], aliases: tuple[str, ...]) -> str:
    for key, value in raw_row.items():
        normalized_key = _normalize(key)
        if any(_normalize(alias) in normalized_key for alias in aliases):
            return value
    return ""


def _extract_table_rows(soup: Any, source_url: str) -> list[dict[str, str]]:
    extracted: list[dict[str, str]] = []
    for table_index, table in enumerate(soup.find_all("table")):
        headers = [
            " ".join(cell.stripped_strings)
            for cell in table.find_all("th")
        ]
        for row_index, row in enumerate(table.find_all("tr")):
            cells = row.find_all(["td", "th"])
            values = [" ".join(cell.stripped_strings) for cell in cells]
            if not values or values == headers:
                continue
            if headers and len(headers) == len(values):
                raw_row = dict(zip(headers, values))
            else:
                raw_row = {
                    f"column_{index + 1}": value
                    for index, value in enumerate(values)
                }
            links = [
                urljoin(source_url, anchor["href"])
                for anchor in row.find_all("a", href=True)
            ]
            curve_link = next(
                (
                    link
                    for link in links
                    if Path(urlparse(link).path).suffix.lower() in FILE_EXTENSIONS
                ),
                "",
            )
            extracted.append(
                {
                    "planet": _field_value(raw_row, ("planet", "name", "object")),
                    "epoch": _field_value(raw_row, ("epoch",)),
                    "mid_transit_time": _field_value(
                        raw_row,
                        ("mid-transit", "mid transit", "timing", "hjd", "bjd"),
                    ),
                    "duration": _field_value(raw_row, ("duration",)),
                    "depth": _field_value(raw_row, ("depth",)),
                    "quality": _field_value(raw_row, ("quality",)),
                    "filter": _field_value(raw_row, ("filter", "band")),
                    "observer": _field_value(raw_row, ("observer", "author")),
                    "light_curve_url": curve_link,
                    "source_url": source_url,
                    "table_index": str(table_index),
                    "row_index": str(row_index),
                    "raw_metadata_json": json.dumps(raw_row, ensure_ascii=False),
                }
            )
    return extracted


def _extract_api_rows(payload: dict[str, Any], source_url: str) -> list[dict[str, str]]:
    extracted: list[dict[str, str]] = []
    for row_index, raw_row in enumerate(payload.get("data") or []):
        extracted.append(
            {
                "planet": str(raw_row.get("name") or ""),
                "epoch": str(raw_row.get("epoch") or ""),
                "mid_transit_time": "",
                "duration": str(raw_row.get("duration") or ""),
                "depth": str(raw_row.get("depth") or ""),
                "quality": "",
                "filter": "",
                "observer": str(raw_row.get("createdBy") or ""),
                "light_curve_url": "",
                "source_url": source_url,
                "table_index": "api",
                "row_index": str(row_index),
                "raw_metadata_json": json.dumps(raw_row, ensure_ascii=False),
            }
        )
    return extracted


def _extract_transit_rows(
    payload: dict[str, Any],
    source_url: str,
    planet_name: str,
) -> list[dict[str, str]]:
    extracted: list[dict[str, str]] = []
    for row_index, raw_row in enumerate(payload.get("transits") or []):
        obs_id = raw_row.get("obsId")
        transit_id = raw_row.get("transId")
        if isinstance(obs_id, int) and isinstance(transit_id, int):
            curve_url = urljoin(
                source_url,
                f"/api/charts/observation/{obs_id}",
            )
        else:
            curve_url = ""
        extracted.append(
            {
                "planet": planet_name,
                "epoch": str(raw_row.get("epoch") or ""),
                "mid_transit_time": str(raw_row.get("hjdMid") or ""),
                "duration": str(raw_row.get("duration") or ""),
                "depth": str(raw_row.get("depth") or ""),
                "quality": str(raw_row.get("dqi") or ""),
                "filter": str(raw_row.get("band") or ""),
                "observer": str(raw_row.get("observer") or ""),
                "light_curve_url": curve_url,
                "source_url": source_url,
                "table_index": "oc_gate_api",
                "row_index": str(row_index),
                "raw_metadata_json": json.dumps(raw_row, ensure_ascii=False),
            }
        )
    return extracted


def _download_candidates(soup: Any, base_url: str) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        url = urljoin(base_url, anchor["href"])
        if url in seen or not _is_public_varastro_url(url):
            continue
        seen.add(url)
        text = " ".join(anchor.stripped_strings).lower()
        suffix = Path(urlparse(url).path).suffix.lower()
        looks_like_file = suffix in FILE_EXTENSIONS
        looks_like_download = any(
            term in text
            for term in ("download", "light curve", "data file")
        )
        if looks_like_file or looks_like_download:
            candidates.append((url, text))
    return candidates


def _filename_from_response(response: requests.Response, index: int) -> str:
    disposition = response.headers.get("content-disposition", "")
    match = re.search(r"filename\*?=(?:UTF-8''|[\"']?)([^\"';]+)", disposition, re.I)
    if match:
        filename = unquote(match.group(1)).strip()
    else:
        filename = Path(urlparse(response.url).path).name
    if not filename or "." not in filename:
        query = parse_qs(urlparse(response.url).query)
        filename = query.get("filename", [f"lightcurve_{index:02d}.dat"])[0]
    return f"{index:02d}_{safe_slug(Path(filename).stem)}{Path(filename).suffix.lower() or '.dat'}"


def _etd_row(
    config: Any,
    *,
    planet_name: str,
    host_star: str,
    source_url: str,
    path: Path | None,
    file_type: str,
    product_type: str,
    status: str,
    error_message: str = "",
    notes: str = "",
) -> dict[str, Any]:
    if path is not None and path.is_file():
        local_path = str(path.resolve().relative_to(config.PROJECT_ROOT.resolve()))
        checksum = sha256_file(path)
        file_size = path.stat().st_size
    else:
        local_path = ""
        checksum = ""
        file_size = ""
    return {
        "collected_at_utc": utc_now(),
        "planet_name": planet_name,
        "host_star": host_star,
        "source_url": source_url,
        "local_path": local_path,
        "file_type": file_type,
        "product_type": product_type,
        "status": status,
        "error_message": error_message,
        "sha256": checksum,
        "file_size_bytes": file_size,
        "notes": notes,
    }


def collect_etd_varastro(
    config: Any,
    session: requests.Session,
    manifest: RawDataManifest,
    logger: logging.Logger,
) -> None:
    logger.info("Starting ETD / VarAstro collection")
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        for planet in config.PLANETS:
            register_error(
                manifest,
                logger,
                source_name=SOURCE_NAME,
                source_url=config.ETD_CATALOG_URL,
                planet_name=planet["planet_name"],
                host_star=planet["host_star"],
                product_type="catalog_search",
                query_or_search_term=planet["planet_name"],
                error=exc,
            )
        return

    for planet in sorted(config.PLANETS, key=lambda item: item["priority"]):
        planet_name = planet["planet_name"]
        host_star = planet["host_star"]
        slug = safe_slug(planet_name)
        html_dir = config.RAW_DATA_DIR / "etd_varastro" / "html_snapshots" / slug
        metadata_dir = (
            config.RAW_DATA_DIR / "etd_varastro" / "extracted_metadata" / slug
        )
        curve_dir = (
            config.RAW_DATA_DIR / "etd_varastro" / "downloaded_lightcurves" / slug
        )
        for directory in (html_dir, metadata_dir, curve_dir):
            directory.mkdir(parents=True, exist_ok=True)

        per_planet_rows: list[dict[str, Any]] = []
        pages: list[tuple[requests.Response, Any]] = []
        consulted_urls: list[str] = []
        errors: list[str] = []
        api_payload: dict[str, Any] | None = None
        observation_api_payload: dict[str, Any] | None = None
        selected_match: dict[str, Any] | None = None

        try:
            response = _get(
                session,
                config,
                config.ETD_CATALOG_URL,
                params={"name": planet_name},
            )
            consulted_urls.append(response.url)
            snapshot_path = html_dir / "catalog_search.html"
            created = _save_html(
                response,
                snapshot_path,
                manifest,
                planet_name=planet_name,
                host_star=host_star,
                product_type="catalog_search_snapshot",
                search_term=planet_name,
            )
            per_planet_rows.append(
                _etd_row(
                    config,
                    planet_name=planet_name,
                    host_star=host_star,
                    source_url=response.url,
                    path=snapshot_path,
                    file_type="html",
                    product_type="catalog_search_snapshot",
                    status="downloaded" if created else "skipped_existing",
                )
            )
            soup = BeautifulSoup(response.content, "lxml")
            pages.append((response, soup))

            api_response = _get(
                session,
                config,
                urljoin(config.ETD_CATALOG_URL, "/api/Search/Exoplanets"),
                params={
                    "pageId": "1",
                    "pageSize": "20",
                    "name": planet_name,
                },
                headers={
                    "Authorization": f"Bearer {session.cookies.get('Token', '')}"
                },
            )
            consulted_urls.append(api_response.url)
            api_path = html_dir / "catalog_search_results.json"
            api_created = save_artifact(
                manifest,
                api_path,
                api_response.content,
                source_name=SOURCE_NAME,
                source_url=api_response.url,
                planet_name=planet_name,
                host_star=host_star,
                file_type="json",
                product_type="catalog_search_api_response",
                query_or_search_term=planet_name,
                notes=(
                    "Unmodified JSON returned by the public endpoint used by "
                    "the VarAstro exoplanet catalog DataTable."
                ),
            )
            per_planet_rows.append(
                _etd_row(
                    config,
                    planet_name=planet_name,
                    host_star=host_star,
                    source_url=api_response.url,
                    path=api_path,
                    file_type="json",
                    product_type="catalog_search_api_response",
                    status="downloaded" if api_created else "skipped_existing",
                )
            )
            api_payload = api_response.json()
            api_rows = api_payload.get("data") or []
            exact_matches = [
                row
                for row in api_rows
                if _normalize(str(row.get("name") or "")) == _normalize(planet_name)
            ]
            selected_match = exact_matches[0] if exact_matches else (
                api_rows[0] if api_rows else None
            )

            detail_url = None
            if selected_match and selected_match.get("id") is not None:
                detail_url = urljoin(
                    config.ETD_CATALOG_URL,
                    f"/en/Exoplanets/{selected_match['id']}",
                )
            if detail_url is None:
                detail_url = _find_planet_detail_url(soup, response.url, planet_name)
            if detail_url and detail_url != response.url:
                detail_response = _get(session, config, detail_url)
                consulted_urls.append(detail_response.url)
                detail_path = html_dir / "planet_detail.html"
                detail_created = _save_html(
                    detail_response,
                    detail_path,
                    manifest,
                    planet_name=planet_name,
                    host_star=host_star,
                    product_type="planet_detail_snapshot",
                    search_term=planet_name,
                )
                per_planet_rows.append(
                    _etd_row(
                        config,
                        planet_name=planet_name,
                        host_star=host_star,
                        source_url=detail_response.url,
                        path=detail_path,
                        file_type="html",
                        product_type="planet_detail_snapshot",
                        status="downloaded" if detail_created else "skipped_existing",
                    )
                )
                pages.append(
                    (
                        detail_response,
                        BeautifulSoup(detail_response.content, "lxml"),
                    )
                )

            if selected_match and selected_match.get("id") is not None:
                observation_api_url = urljoin(
                    config.ETD_CATALOG_URL,
                    f"/api/OcGate/Exoplanets/{selected_match['id']}",
                )
                observation_response = _get(
                    session,
                    config,
                    observation_api_url,
                    headers={
                        "Authorization": f"Bearer {session.cookies.get('Token', '')}"
                    },
                )
                candidate_observation_payload = observation_response.json()
                private_count = sum(
                    bool(row.get("isPrivate"))
                    for row in candidate_observation_payload.get("transits") or []
                )
                if private_count:
                    raise RuntimeError(
                        "The anonymous observations endpoint unexpectedly returned "
                        f"{private_count} private records; response was not saved"
                    )
                observation_api_payload = candidate_observation_payload
                observation_api_path = metadata_dir / "observations_raw.json"
                observation_api_created = save_artifact(
                    manifest,
                    observation_api_path,
                    observation_response.content,
                    source_name=SOURCE_NAME,
                    source_url=observation_response.url,
                    planet_name=planet_name,
                    host_star=host_star,
                    file_type="json",
                    product_type="public_transit_observations_api_response",
                    query_or_search_term=planet_name,
                    notes=(
                        "Unmodified JSON returned by the public observations "
                        "endpoint used by the VarAstro detail page."
                    ),
                )
                per_planet_rows.append(
                    _etd_row(
                        config,
                        planet_name=planet_name,
                        host_star=host_star,
                        source_url=observation_response.url,
                        path=observation_api_path,
                        file_type="json",
                        product_type="public_transit_observations_api_response",
                        status=(
                            "downloaded"
                            if observation_api_created
                            else "skipped_existing"
                        ),
                    )
                )
        except Exception as exc:
            errors.append(str(exc))
            register_error(
                manifest,
                logger,
                source_name=SOURCE_NAME,
                source_url=config.ETD_CATALOG_URL,
                planet_name=planet_name,
                host_star=host_star,
                product_type="catalog_or_detail_snapshot",
                query_or_search_term=planet_name,
                error=exc,
            )
            per_planet_rows.append(
                _etd_row(
                    config,
                    planet_name=planet_name,
                    host_star=host_star,
                    source_url=config.ETD_CATALOG_URL,
                    path=None,
                    file_type="html",
                    product_type="catalog_or_detail_snapshot",
                    status="failed",
                    error_message=str(exc),
                )
            )

        observations: list[dict[str, str]] = []
        download_links: list[tuple[str, str]] = []
        seen_download_urls: set[str] = set()
        for page_response, soup in pages:
            observations.extend(_extract_table_rows(soup, page_response.url))
            for candidate in _download_candidates(soup, page_response.url):
                if candidate[0] not in seen_download_urls:
                    seen_download_urls.add(candidate[0])
                    download_links.append(candidate)

        if observation_api_payload is not None:
            observations = _extract_transit_rows(
                observation_api_payload,
                observation_response.url,
                str(selected_match.get("name") or planet_name),
            ) + observations
        elif api_payload is not None:
            observations = _extract_api_rows(api_payload, api_response.url) + observations

        observations_path = metadata_dir / "observations.csv"
        observations_content = csv_bytes(observations, OBSERVATION_COLUMNS)
        observations_path = versioned_path(
            observations_path,
            observations_content,
            "api",
        )
        observations_created = save_artifact(
            manifest,
            observations_path,
            observations_content,
            source_name=SOURCE_NAME,
            source_url=consulted_urls[-1] if consulted_urls else config.ETD_CATALOG_URL,
            planet_name=planet_name,
            host_star=host_star,
            file_type="csv",
            product_type="extracted_public_metadata",
            query_or_search_term=planet_name,
            notes=(
                "Metadata extracted from public HTML tables. raw_metadata_json "
                "preserves each source row without inferred or estimated values."
            ),
        )
        per_planet_rows.append(
            _etd_row(
                config,
                planet_name=planet_name,
                host_star=host_star,
                source_url=consulted_urls[-1] if consulted_urls else config.ETD_CATALOG_URL,
                path=observations_path,
                file_type="csv",
                product_type="extracted_public_metadata",
                status="downloaded" if observations_created else "skipped_existing",
                notes=f"{len(observations)} HTML table rows extracted.",
            )
        )

        for index, (url, link_text) in enumerate(
            download_links[: config.MAX_ETD_LIGHTCURVES_PER_PLANET],
            start=1,
        ):
            try:
                response = _get(session, config, url)
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" in content_type:
                    raise RuntimeError(
                        "Candidate download URL returned HTML instead of a data file"
                    )
                filename = _filename_from_response(response, index)
                destination = curve_dir / filename
                created = save_artifact(
                    manifest,
                    destination,
                    response.content,
                    source_name=SOURCE_NAME,
                    source_url=response.url,
                    planet_name=planet_name,
                    host_star=host_star,
                    file_type=destination.suffix.lstrip("."),
                    product_type="ground_based_light_curve",
                    query_or_search_term=planet_name,
                    notes=f"Public link text: {link_text}",
                )
                per_planet_rows.append(
                    _etd_row(
                        config,
                        planet_name=planet_name,
                        host_star=host_star,
                        source_url=response.url,
                        path=destination,
                        file_type=destination.suffix.lstrip("."),
                        product_type="ground_based_light_curve",
                        status="downloaded" if created else "skipped_existing",
                        notes=f"Public link text: {link_text}",
                    )
                )
            except Exception as exc:
                errors.append(f"{url}: {exc}")
                register_error(
                    manifest,
                    logger,
                    source_name=SOURCE_NAME,
                    source_url=url,
                    planet_name=planet_name,
                    host_star=host_star,
                    product_type="ground_based_light_curve",
                    query_or_search_term=planet_name,
                    error=exc,
                )
                per_planet_rows.append(
                    _etd_row(
                        config,
                        planet_name=planet_name,
                        host_star=host_star,
                        source_url=url,
                        path=None,
                        file_type="",
                        product_type="ground_based_light_curve",
                        status="failed",
                        error_message=str(exc),
                    )
                )

        api_curve_candidates = []
        if observation_api_payload is not None:
            api_curve_candidates = [
                row
                for row in observation_api_payload.get("transits") or []
                if isinstance(row.get("obsId"), int)
                and isinstance(row.get("transId"), int)
                and not row.get("isPrivate")
            ][: config.MAX_ETD_LIGHTCURVES_PER_PLANET]

        for index, row in enumerate(api_curve_candidates, start=1):
            obs_id = row["obsId"]
            transit_id = row["transId"]
            data_version = row.get("dataVersion") or ""
            curve_url = urljoin(
                config.ETD_CATALOG_URL,
                f"/api/charts/observation/{obs_id}",
            )
            curve_params = {
                "origrawheader": "true",
                "airmass": "true",
                "v": str(data_version),
                "transid": str(transit_id),
            }
            destination = curve_dir / (
                f"{index:02d}_observation_{obs_id}_transit_{transit_id}.json"
            )
            try:
                if destination.exists():
                    manifest.record_artifact(
                        path=destination,
                        created=False,
                        source_name=SOURCE_NAME,
                        source_url=curve_url,
                        planet_name=planet_name,
                        host_star=host_star,
                        file_type="json",
                        product_type="ground_based_light_curve_api_json",
                        query_or_search_term=planet_name,
                    )
                    created = False
                    response_url = curve_url
                else:
                    curve_response = _get(
                        session,
                        config,
                        curve_url,
                        params=curve_params,
                        headers={
                            "Authorization": (
                                f"Bearer {session.cookies.get('Token', '')}"
                            )
                        },
                    )
                    curve_payload = curve_response.json()
                    if not isinstance(curve_payload.get("photometry"), list):
                        raise RuntimeError(
                            "Observation endpoint returned no photometry array"
                        )
                    created = save_artifact(
                        manifest,
                        destination,
                        curve_response.content,
                        source_name=SOURCE_NAME,
                        source_url=curve_response.url,
                        planet_name=planet_name,
                        host_star=host_star,
                        file_type="json",
                        product_type="ground_based_light_curve_api_json",
                        query_or_search_term=planet_name,
                        notes=(
                            "Unmodified public VarAstro chart API response; "
                            "includes photometry and the uploaded raw header "
                            "when the service provides it."
                        ),
                    )
                    response_url = curve_response.url
                per_planet_rows.append(
                    _etd_row(
                        config,
                        planet_name=planet_name,
                        host_star=host_star,
                        source_url=response_url,
                        path=destination,
                        file_type="json",
                        product_type="ground_based_light_curve_api_json",
                        status="downloaded" if created else "skipped_existing",
                        notes=(
                            "Public API response used by the VarAstro observation "
                            "chart; not converted to CSV or altered."
                        ),
                    )
                )
            except Exception as exc:
                errors.append(f"{curve_url}: {exc}")
                register_error(
                    manifest,
                    logger,
                    source_name=SOURCE_NAME,
                    source_url=curve_url,
                    planet_name=planet_name,
                    host_star=host_star,
                    product_type="ground_based_light_curve_api_json",
                    query_or_search_term=planet_name,
                    error=exc,
                )
                per_planet_rows.append(
                    _etd_row(
                        config,
                        planet_name=planet_name,
                        host_star=host_star,
                        source_url=curve_url,
                        path=None,
                        file_type="json",
                        product_type="ground_based_light_curve_api_json",
                        status="failed",
                        error_message=str(exc),
                    )
                )

        notes = (
            f"# ETD / VarAstro collection notes for {planet_name}\n\n"
            f"- Search term: `{planet_name}` (host star `{host_star}`)\n"
            f"- URLs consulted: {', '.join(consulted_urls) if consulted_urls else 'none'}\n"
            f"- Public HTML table rows extracted: {len(observations)}\n"
            f"- Candidate public data links found in HTML: {len(download_links)}\n"
            f"- Public observation API curves selected: {len(api_curve_candidates)}\n"
            f"- Download limit: {config.MAX_ETD_LIGHTCURVES_PER_PLANET}\n"
            "- No login, private endpoint, browser automation, or protection bypass was used.\n"
            "- ETD observations are associated with the parent star in VarAstro; "
            "the public exoplanet page is used to establish the planet relationship.\n"
            "- Curve JSON files are unmodified responses from the public chart API, "
            "not exports of the observer's originally uploaded file.\n"
            f"- Errors or limitations: {'; '.join(errors) if errors else 'none recorded'}\n"
        )
        notes_path = metadata_dir / "notes.md"
        notes_path = versioned_path(notes_path, notes.encode("utf-8"), "api")
        notes_created = atomic_write_text(notes_path, notes)
        manifest.record_artifact(
            path=notes_path,
            created=notes_created,
            source_name=SOURCE_NAME,
            source_url=consulted_urls[-1] if consulted_urls else config.ETD_CATALOG_URL,
            planet_name=planet_name,
            host_star=host_star,
            file_type="md",
            product_type="collection_notes",
            query_or_search_term=planet_name,
        )
        per_planet_rows.append(
            _etd_row(
                config,
                planet_name=planet_name,
                host_star=host_star,
                source_url=consulted_urls[-1] if consulted_urls else config.ETD_CATALOG_URL,
                path=notes_path,
                file_type="md",
                product_type="collection_notes",
                status="downloaded" if notes_created else "skipped_existing",
            )
        )

        etd_manifest_path = (
            config.RAW_DATA_DIR
            / "etd_varastro"
            / "manifests"
            / f"{slug}_manifest.csv"
        )
        manifest_content = csv_bytes(per_planet_rows, ETD_MANIFEST_COLUMNS)
        etd_manifest_path = versioned_path(
            etd_manifest_path,
            manifest_content,
            "api",
        )
        save_artifact(
            manifest,
            etd_manifest_path,
            manifest_content,
            source_name=SOURCE_NAME,
            source_url=consulted_urls[-1] if consulted_urls else config.ETD_CATALOG_URL,
            planet_name=planet_name,
            host_star=host_star,
            file_type="csv",
            product_type="source_manifest",
            query_or_search_term=planet_name,
        )
        logger.info(
            "ETD processed %s: %d metadata rows, %d download candidates",
            planet_name,
            len(observations),
            len(download_links) + len(api_curve_candidates),
        )
    logger.info("Finished ETD / VarAstro collection")
