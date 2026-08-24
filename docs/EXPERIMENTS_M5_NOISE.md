# Experimentos Avançados: M5 (Modelo Físico), Sensibilidade de Priors e Injeção de Ruído

Esta documentação explica em detalhes os três avanços metodológicos finais do pipeline bayesiano construído neste repositório. O objetivo destes testes é validar a robustez estatística do amostrador NUTS e provar a adequação da técnica para a obtenção de parâmetros físicos precisos (como a relação de raios planetários $R_p/R_s$), além de testar a resiliência do modelo contra condições sub-ótimas (Priors ruins e ruído vermelho).

---

## 1. M5: O Modelo Físico Completo (Mandel & Agol)

**Script:** `scripts/run_bayesian_physical_transit.py`

Os modelos M1 a M3 utilizaram formas geométricas puras (caixas, regressões e trapézios) para estimar a queda de luz. O modelo **M5** eleva o rigor astrofísico ao incorporar a aproximação física completa desenvolvida por Mandel & Agol (2002), acoplada à biblioteca `exoplanet`.

### Por que M5 é Diferente?
*   **Limb Darkening (Escurecimento de Limbo):** Estrelas não são discos de brilho uniforme; elas são mais escuras nas bordas. O M5 utiliza um modelo de escurecimento quadrático (`QuadLimbDark`), alinhado à física da fotosfera estelar.
*   **Órbita Kepleriana:** Ele não estima "tempos de ingresso", e sim a física real: o semi-eixo maior escalar ($a$), o parâmetro de impacto ($b$) e a relação de raio planetário/estelar ($r$).
*   **Convergência NUTS:** Como a biblioteca `exoplanet` é otimizada em PyTensor, conseguimos rodar o *No-U-Turn Sampler* com gradientes exatos das operações astrofísicas (escritas em C++ de baixo nível).

### Requisitos Especiais de Sistema
O modelo M5 e a biblioteca `exoplanet` **exigem compilação C++ ativa (gcc/g++)**. No ambiente Windows (Python 3.13), compiladores C++ muitas vezes apresentam problemas (como erros de segmentação no PyTensor). Portanto, **o M5 deve ser executado no WSL (Windows Subsystem for Linux) ou Google Colab**.

Para executar via WSL:
```bash
# Dentro do WSL, certifique-se de ter um ambiente python ativo:
pip install -r requirements.txt exoplanet exoplanet-core
python scripts/run_bayesian_physical_transit.py
```

---

## 2. Injeção Artificial de Ruído (Red Noise Simulation)

**Script:** `scripts/run_bayesian_noise_injection.py`

Em astronomia, dados reais raramente contêm apenas "ruído branco" (estatístico, fácil de lidar). Eles contêm **Ruído Vermelho (Correlated Noise)** gerado por pulsações estelares, variações térmicas no telescópio, e manchas na estrela que rotacionam.

### O Experimento
No script de Injeção de Ruído, carregamos os dados perfeitamente limpos da camada "Gold", e os "sujamos" propositalmente antes de alimentar o modelo M3/M5:
```python
# Ruído Vermelho (Senoidal de baixa frequência)
red_noise = 0.003 * np.sin(2 * np.pi * phase_array / 0.1)

# Ruído Branco (Erro instrumental alto)
white_noise = np.random.normal(0, 0.002, size=len(phase_array))

prepared["normalized_flux"] += red_noise + white_noise
```
*   **Objetivo:** Provar que a Inferência Bayesiana com um bom termo adaptativo de erro (`extra_sigma`) consegue modelar as incertezas observacionais (Likelihood) perfeitamente, ainda sendo capaz de estimar a profundidade (depth) verdadeira da ocultação.
*   **Resultado Esperado:** O modelo ajusta a variância total da Posterior e descobre o trânsito do planeta (Efeito de Marginalização do Ruído).

---

## 3. Teste de Sensibilidade (O Experimento de Shrinkage)

**Script:** `scripts/run_bayesian_sensitivity.py`

O maior ponto de ataque contra modelos bayesianos é que "Priors ruins geram predições ruins". O teste de sensibilidade prova matematicamente o fenômeno de **Bayesian Shrinkage**.

### O Experimento
Nós propositalmente colocamos Priors terríveis e absurdos:
```python
# O baseline real é 1.0 (Fluxo 100%), mas dizemos ao modelo que achamos que é 1.5!
baseline = pm.Normal("baseline", mu=1.5, sigma=0.01)

# A profundidade real do planeta é ~0.006, mas dizemos ao modelo que a estrela vai apagar quase inteira (0.5)!
depth = pm.Normal("depth", mu=0.5, sigma=0.01)
```
*   **Objetivo:** Ao rodar o amostrador, a Força da Verossimilhança (*Likelihood*) extraída dos dados originais (Camada Gold) puxa as estimativas violentamente de volta para a realidade, esmagando os "chutes" ruins (Shrinkage).
*   **Resultado Esperado:** As distribuições Posteriores vão convergir para uma profundidade de `0.006` e baseline `1.0`, e a taxa de divergência pode ou não aumentar temporariamente no processo de *Tuning* inicial, provando a resiliência do pipeline.

---

### Conclusão e Replicabilidade
Para replicar os experimentos (garantindo que `HAT-P-7 b` esteja configurado no `gold_data_config.py`):
1. Execute `run_bayesian_physical_transit.py` para obter o modelo ideal de `exoplanet` (somente em WSL/Linux).
2. Execute `run_bayesian_noise_injection.py` para visualizar o modelo trabalhando com dados ruidosos.
3. Execute `run_bayesian_sensitivity.py` para visualizar a convergência forçada após um "prior ruim".

