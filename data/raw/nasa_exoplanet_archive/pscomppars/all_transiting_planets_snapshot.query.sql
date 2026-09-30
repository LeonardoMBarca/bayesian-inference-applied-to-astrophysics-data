SELECT * FROM pscomppars WHERE discoverymethod = 'Transit' AND pl_orbper IS NOT NULL AND (pl_rade IS NOT NULL OR pl_trandep IS NOT NULL) ORDER BY pl_name
