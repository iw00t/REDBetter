![REDBetter Logo](logo.jpg)

## Introduction

This repository contains my personal fork of the REDBetter script, originally developed for What.CD by zacharydenton and updated by Mechazawa.

---
REDBetter is a script which searches your torrent download directory for any FLAC torrents which do not have transcodes, then automatically transcodes and uploads the torrents to redacted.ch.

## Dependencies

* Python 2.7 or newer
* `mktorrent`
* `mechanize`, `mutagen`, `requests` and `Unidecode` Python modules
* `lame`, `sox` and `flac`


## Installation Instructions

#### 1. Install Python

Python is available [here](https://www.python.org/downloads/).


#### 2. Install `mktorrent`

`mktorrent` must be built from source, rather than installed using a package manager. For Linux systems, run the following commands in a temporary directory:

~~~~
$> git clone git@github.com:Rudde/mktorrent.git
$> cd mktorrent
$> make && sudo make install
~~~~

If you are on a seedbox and you lack the privileges to install packages, you are best off contacting your seedbox provider and asking them to install the listed packages.

#### 3. Install `mechanize`, `mutagen`, `requests` and `Unidecode` Python modules

Depending on your user privileges you may need to use sudo, as shown below

~~~~
sudo -H pip install -r requirements.txt
~~~~


#### 4. Install `lame`, `sox` and `flac`

These should all be available on your package manager of choice:
  * Debian: `sudo apt-get install lame sox flac`
  * Ubuntu: `sudo apt install lame sox flac`
  * macOS: `brew install lame sox flac`



## Configuration
Run REDBetter by running the script included when you cloned the repository:

    $> ./redactedbetter

You will receive a notification stating that you should edit the configuration file located at:

    ~/.redactedbetter/config

Open this file in your preferred text editor, and configure as desired. The options are as follows:
* `username`: Your redacted.ch username.
* `password`: Your redacted.ch password.
* `data_dir`: The directory where your torrent downloads are stored.
* `output_dir`: The directory where the transcoded torrent files will be stored. If left blank, it will use the value of `data_dir`.
* `torrent_dir`: The directory where the generated `.torrent` files are stored.
* `formats`: A comma space (`, `) separated list of formats you'd like to transcode to. By default, this will be `flac, v0, 320`. `flac` is included because REDBetter supports converting 24-bit FLAC to 16-bit FLAC. Note that `v2` is not included deliberately - v0 torrents trump v2 torrents per redacted rules.
* `media`: A comma space (`, `) separated list of media types you want to consider for transcoding. The default value is all redacted lossless formats, but if you want to transcode only CD and vinyl media, for example, you would set this to `cd, vinyl`.
* `24bit_behaviour`: Defines what happens when the program encounters a FLAC that it thinks is 24-bit. If it is set to `2`, every FLAC that has a bit depth of 24 will be silently re-categorized. If it is set to `1`, a prompt wil appear. The default is `0` which ignores these occurrences.

## Usage
~~~~
usage: redactedbetter [-h] [-s] [-j THREADS] [--config CONFIG] [--cache CACHE]
                      [-U] [-E] [--version]
                      [release_urls [release_urls ...]]

positional arguments:
  release_urls          the URL where the release is located (default: None)

optional arguments:
  -h, --help            show this help message and exit
  -s, --single          only add one format per release (useful for getting
                        unique groups) (default: False)
  -j THREADS, --threads THREADS
                        number of threads to use when transcoding (default: 3)
  --config CONFIG       the location of the configuration file (default:
                        /home/taylor/.redactedbetter/config)
  --cache CACHE         the location of the cache (default:
                        /home/taylor/.redactedbetter/cache)
  -U, --no-upload       don't upload new torrents (in case you want to do it
                        manually) (default: False)
  -E, --no-24bit-edit   don't try to edit 24-bit torrents mistakenly labeled
                        as 16-bit (default: False)
  --version             show program's version number and exit
~~~~

### Examples

To transcode and upload everything you have in your download directory (it could take a while):

    $> ./redactedbetter

To transcode and upload a specific release (provided you have already downloaded the FLAC and it is located in your `data_dir`):

    $> ./redactedbetter http://redacted.ch/torrents.php?id=1000\&torrentid=1000000

Note that if you specify a particular release, redactedbetter will ignore your configuration's media types and attempt to transcode the releases you have specified regardless of their media type (so long as they are lossless types).

REDBetter caches the results of your transcodes, and will skip any transcodes it believes it's already finished. This makes subsequent runs much faster than the first, especially with large download directories. However, if you do run into errors when running the script, sometimes you will find that the cache thinks the torrent it crashed on previously was uploaded - so it skips it. A solution would be to manually specify the release as mentioned above. If you have multiple issues like this, you can remove the cache:

    $> ./redactedbetter ~/.redactedbetter/cache

Beware though, this will cause the script to re-check every download as it does on the first run.

### Docker example

~~~
  $> cp docker-compose.override.example.yml docker-compose.override.yml
  $> $EDITOR docker-compose.override.yml

    # Change the volume mounts to your custom values
    # Use your own 'user: uid:gid' pair

  $> mkdir ~/.redactedbetter
  $> chmod go-rx ~/.redactedbetter
  $> $EDITOR ~/.redactedbetter/config

    # Configure your username and password. Paths in this configuration file
    # are valid inside the container, you shouldn't have to change them if you
    # properly configured the volumes previously. (docker-compose.override.yml)

  $> docker-compose build
  $> docker-compose run --rm redbetter
~~~

## Bugs and feature requests

If you have any issues using the script, or would like to suggest a feature, feel free to open an issue in the issue tracker, *provided that you have searched for similar issues already*.
