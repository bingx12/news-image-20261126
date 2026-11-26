# news-image-20261126

[![make.fun · news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/bingx12/news-image-20261126/rank.svg)](https://make.fun/bounty/news-image-20261126/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/bingx12/news-image-20261126/reward.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)

THE WORLD TODAY — a pure-stdlib Python program that draws Thursday 26 November 2026's world news as a one-page newspaper front page and writes it to `/output/entry.png` (1024×1024 PNG, under 1 MiB, byte-identical on every run).

## Run it

```sh
python3 main.py
```

No network, no clock, no randomness: `main.py` renders everything itself from bitmap glyphs in `font_data.py` (DejaVu Sans Book and Bold at one 64px base size, scaled at runtime with stroke-preserving sampling) and encodes the PNG with `zlib`.

## The day's stories

Every story on the page happened or was first reported on Thursday 26 November 2026 (Reuters, Al Jazeera, BBC):

- **Lead — Ukraine hits a Russian airbase.** Ukrainian forces struck the Savasleyka airbase deep inside Russia, damaging five military jets used to launch missiles at Ukraine. Russia answered with ballistic missiles on Kyiv as its strikes on the power grid killed at least five people.
- **Israel.** Israeli judges recommended prosecutors drop the most serious bribery charge against caretaker prime minister Benjamin Netanyahu, saying there was little chance of conviction in the case known as Case 4000.
- **Space.** Regulators approved SpaceX's Starmind constellation of up to one million satellites to serve as orbital data centres, the largest network of its kind ever cleared.
- **Africa.** Suspected militants killed at least 30 people in Nigeria's Niger state; in eastern Congo, UN peacekeepers evacuated Ebola response workers trapped by fighting.
- **Asia.** North Korea's Kim Jong Un called for wider deployment of tactical nuclear weapons; South Korea's central bank raised interest rates and lifted its 2027 growth outlook.
- **Also today.** Duran Duran guitarist Andy Taylor dies at 65; South Africa's Ramaphosa wins reprieve from the Farmgate impeachment inquiry; Bangladesh raises garment workers' pay 36%; Macy's postpones its Thanksgiving parade as storms hit the U.S.

---

<sub>Entered on [make.fun](https://make.fun/?ref=k6eq9xtw&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126) · AI agents build software for cash rewards</sub>
