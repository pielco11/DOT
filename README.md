# DOT - Darknet OSINT Transform

[dashboard](screenshot_12.png)

This is the repo of DOT Maltego Transform.
Finally the right name.

## What does this do?

It fetches: open ports, banners, emails, btc addresses, linked onions domains and other (soon).

## Where are the infos stored?

The infos are stored in a database, which is in a server controlled by us, so that you can do a reverse search (e.g. email address -> domains).

## How can I play with this?

[This](https://cetas.paterva.com/TDS/runner/showseed/fpoldiklLZnPm7) is the link that you need to add this set of transforms to your hub. Some transforms are not ready to run, these are `onionPGPKeys`. `onionIpAddress` and `onionRelatedDomains`. If you run one of these three transform, it will return 0 entities so don't worry about possible errors.

## Latest update
Added a new transform `report issue`, please use **only** to report which entities return "return XML could not be parsed" and specify: type of the entity (email, bitcoin,...) and the value (e.g. spaghetti@pizza.it).

## Contact

For every request don't hesitate to open an issue. If you prefer contacting us in private you can do it via Twitter or keybase.
