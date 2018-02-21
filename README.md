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
- Added the entity to the configuration seed;
- New data is ready to come.
- ~~Feb 20, about 23:30 CET: service under maintenance~~ Feb 21, 10:00 CET: service up & running

## Contact

For every request don't hesitate to open an issue. If you prefer contacting us in private you can do it via Twitter or keybase. 
