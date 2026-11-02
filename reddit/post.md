## Title

[OC] Every tsunami on record: 1,699 since 1610 BC, mapped with the 32,628 places their water reached. 72% start with an earthquake, the highest ran 524 m up a mountain, and one day in 2004 accounts for 42% of all recorded deaths

## Body

I mapped every tsunami NOAA's Global Historical Tsunami Database rates as definite or probable, 1,699 of them, and the places where their water was recorded. 67% began on the rim of the Pacific, and 79% involved an earthquake. The deaths are concentrated: 545,939 tsunami deaths are recorded, 42% of them from the 2004 Indian Ocean tsunami; the Indian Ocean has 6% of the tsunamis but 50% of the deaths. The highest water comes from landslides into fjords, led by Lituya Bay in Alaska (524 m in 1958). Waves crossing oceans move at about 680 km/h: Chile 1960 reached Japan in 22.4 hours. Caveats: the record grows from 63 tsunamis in the 1600s to 718 in the 1900s, which is better recording, not more tsunamis; old death tolls are estimates; deaths are the tsunami's own, not the earthquake's. Interactive map with a time slider, a tour of famous waves and lines from each source to every place it reached: https://maps.tristanhotham.com/tsunamis/

## Source comment

Source: NOAA NCEI/WDS Global Historical Tsunami Database (doi:10.7289/V5PN93H7, public domain), events and runups from the NCEI Hazard Service API, 2026. Tsunamis = NCEI validity 3 (probable) or 4 (definite); deaths = NCEI's tsunami deaths; runups flagged doubtful dropped. Plate boundaries: Bird (2003) PB2002. Outlines: Natural Earth.

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: https://maps.tristanhotham.com/tsunamis/
Paper: https://doi.org/10.5281/zenodo.23873531
Blog post: https://blog.tristanhotham.com/2026/10/31/tsunamis/
