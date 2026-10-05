# Painel Brasileirão 2026

Painel do Campeonato Brasileiro 2026 com duas visões, para qualquer um dos 20 clubes:

- **Painel**: posição, pontos, aproveitamento, saldo, últimos jogos, distância para líder/G6/Z4, classificação completa e próximos jogos. Filtro de jogos em casa, fora ou todos.
- **Rumo à Meta**: quantos pontos faltam para uma meta (45 por padrão), chances de vitória em cada jogo restante e simulação dos resultados.

As cores da página mudam de acordo com o clube escolhido. Links diretos: `#sao-paulo`, `#meta-palmeiras` etc.

## Como atualizar

Tudo é calculado a partir de `dados/jogos.csv`, uma linha por jogo. Colunas: `competicao, fase, data, hora, mandante, visitante, gols_mandante, gols_visitante, observacao`.

Os jogos do Brasileirão são atualizados a partir do [openfootball](https://github.com/openfootball/football.json) com:

```
python3 scripts/atualizar_openfootball.py
```

O script atualiza datas, horários e placares, nunca apaga um placar já preenchido e não mexe nos jogos de outras competições. Uma tarefa agendada roda esse script a cada 3 dias e faz o commit; o GitHub Pages republica sozinho em cerca de um minuto.

Para corrigir ou adiantar um resultado à mão, basta editar `gols_mandante` e `gols_visitante` na linha do jogo e fazer o commit.

## Como as probabilidades são calculadas

Modelo de Dixon e Coles (1997): os gols esperados de cada time saem do ataque e da defesa em casa e fora nesta edição do Brasileirão, com peso maior para jogos recentes (meia-vida de 180 dias) e notas puxadas para a média da liga. As chances de vitória, empate e derrota vêm de uma distribuição de Poisson com a correção de Dixon e Coles para 0x0, 1x0, 0x1 e 1x1 (parâmetro ρ estimado com os placares da temporada). A chance de bater a meta vem de 20 mil simulações. A explicação completa, com exemplo ao vivo, está na aba "Como calculamos" do painel. São estimativas, não previsões.

## Fontes

- Brasileirão: [openfootball/football.json](https://github.com/openfootball/football.json) (domínio público)
- Demais competições do São Paulo: Goal e Arquibancada Tricolor

Projeto de fã, não oficial e sem vínculo com nenhum clube. As cores apenas evocam as de cada time; não há escudos nem marcas.
