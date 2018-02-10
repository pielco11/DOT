# TOT - Tor OSINT Transform

This is the repo of TOT Maltego Transform.
Renamed this from *OSMT* to *TOT* because now this runs on our written tools.

## What does this do?

It fetches: open ports, banners, emails, btc addresses, linked onions domains and other (soon).

## Where are the infos stored?

The infos are stored in a database, which is in a server controlled by us, so that you can do a reverse search (e.g. email address -> domains).

## How can I play with this?

[This](https://cetas.paterva.com/TDS/runner/showseed/fpoldiklLZnPm7) is the link that you need to add this set of transforms to your hub. Some transforms are not ready to run, these are `onionPGPKeys`. `onionIpAddress` and `onionRelatedDomains`. If you run one of these three transform, it will return 0 entities so don't worry about possible errros.

## Latest update
Changed the input entity for almost every transform. Open Maltego, select `Import Entities` and choose `entity.mtz`.
Changed UI title for transforms, more clear now.

Tip: if you don't like these changes, just don't update the transform and everything should work as well since "core" stuff didn't change.

## Contact

For every request don't hesitate to open an issue. If you prefer contacting us in private you can do it via Twitter or keybase. 
