# cosplaythots-downloader
Simple downloader for storing cosplaythots content. Its loading is sequential so it is a little slow.

Can download single entities (`/p/XXXXX`) or multiple:
* Copyright (or just tags idk) (`/f/XXXXX`)
* Model (`/m/XXXXX`)
* Character (`/c/XXXXX`)

```
usage: cosplaythots-downloader [-h] [-o OUTPUT] [-s SKIP] [-c COUNT] urls [urls ...]

positional arguments:
  urls

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory
  -s SKIP, --skip SKIP  Categories skip count
  -c COUNT, --count COUNT
                        Categories downloading count
```

# Details

Due to scroll lazy loading on pages for getting entites uses GET request to page with `?page=<n>` suffix where n is page number. It will increases while result contains 10 entites or more.

For getting images uses POST request to `https://cosplaythots.com/cms/load-more-photos.php` with json body. Aproximatly model:
| Key | Type | Default value | Description |
|-|-|-|-|
| owner_id* | string | - | Uploader ID(?) |
| album_id* | string | - | Album ID |
| download  | int    | 0 | If not =1 return empty array |
| download_id | int | *unknown* | |
| offset      | int | 0 | Skip offset for images |
| limit       | int | *unknown* | Max images count to get |
| counter     | int | *unknown* | |

Owner and album ids are obtained from preload image (`head link[rel="preload"]`). Request returns json example:
```json
{
  "photos": [
    {
      "html": "<DIV HTML WITH LINK TO IMAGE>",
      "counter": 123
    },
    ...
  ]
}
```

Names for category directory obtained from page title before *leaked from*.
Names for entity directory obtained from tags (`body > div > center > a.btn`).
