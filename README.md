# Painel Brasileirão 2026

Painel do Campeonato Brasileiro 2026 com duas visões, para qualquer um dos 20 clubes:

- **Painel**: posição, pontos, aproveitamento, saldo, últimos jogos, distância para líder/G6/Z4, classificação completa e próximos jogos. Filtro de jogos em casa, fora ou todos.
- **Rumo à Meta**: quantos pontos faltam para uma meta (45 por padrão), chances de vitória em cada jogo restante e simulação dos resultados.

As cores da página mudam de acordo com o clube escolhido. Links diretos: `#sao-paulo`, `#meta-palmeiras` etc.

## Como atualizar

Somente o Brasileirão 2026 entra no painel: a base não tem jogos de outras competições.

Tudo é calculado a partir de `dados/jogos.csv`, uma linha por jogo. Colunas: `competicao, fase, data, hora, mandante, visitante, gols_mandante, gols_visitante, observacao`.

Os jogos do Brasileirão são atualizados automaticamente pela API pública de placares da ESPN (sem chave de acesso). O workflow `.github/workflows/atualizar-resultados.yml` roda a cada 3 dias às 07:30 (horário de Brasília) e executa:

```
python3 scripts/atualizar_resultados.py
```

O script preenche os placares de jogos encerrados, atualiza datas e horários de jogos futuros e marca adiamentos. Ele nunca apaga nem sobrescreve um placar já preenchido e para sem gravar nada se a API discordar de muitos placares já conhecidos. Quando há mudança, o próprio workflow faz o commit e o GitHub Pages republica o site em cerca de um minuto.

Para rodar na hora, abra a aba **Actions** do repositório, escolha **Atualizar resultados** e clique em **Run workflow**.

Para corrigir ou adiantar um resultado à mão, basta editar `gols_mandante` e `gols_visitante` na linha do jogo e fazer o commit.

## Como as probabilidades são calculadas

Modelo de Dixon e Coles (1997): os gols esperados de cada time saem do ataque e da defesa em casa e fora nesta edição do Brasileirão, com peso maior para jogos recentes (meia-vida de 180 dias) e notas puxadas para a média da liga. As chances de vitória, empate e derrota vêm de uma distribuição de Poisson com a correção de Dixon e Coles para 0x0, 1x0, 0x1 e 1x1 (parâmetro ρ estimado com os placares da temporada). A chance de bater a meta vem de 20 mil simulações. A explicação completa, com exemplo ao vivo, está na aba "Como calculamos" do painel. São estimativas, não previsões.

## Fontes

- Brasileirão: API pública de placares da ESPN (atualização automática); tabela inicial a partir do [openfootball/football.json](https://github.com/openfootball/football.json)

Projeto de fã, não oficial e sem vínculo com nenhum clube. As cores apenas evocam as de cada time; não há escudos nem marcas.
