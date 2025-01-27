# GWW Reservoir Anomalies

With this python app you can calculate monthly reservoir storage anomalies using global water watch data. The app is available as an command-line-interface (CLI).

## How to
The GWW-Anomalies CLI can be used with a Python interpreter or through Docker.

### Python
For using the CLI with Python you first need to install the right packages. Use pip or conda to install the packages in the requirements.txt or environment.yml.

```
pip install requirements.txt 
```
or

```
conda env create -f environment.yml
conda activate gww_anomalies
```

Finally you need to install this Python project in your environment:
```
pip install .
```

The CLI is then accessible by running the cli.py file.

### Docker
If you have docker installed you can also use this app through Docker. This app requires the data that is present in the data folder in this repository. With Docker it easy to package the data with the code in one Docker image, while also taking care that all the right packages are installed.

To build the docker image change directory to this repository and run the following command in a terminal where docker is installed, you maybe need sudo to call it:
```
docker compose build
```
To run the service:

```
docker compose run --rm gww_anomalies  [-h] [-r RESERVOIR_IDS_FILE] [-m MONTH] [-v | --as-vector | --no-as-vector]
```
the commands after 'gww_anomalies' are optional commands that are passed to gww_anomalies/cli.py, more on that below.

### CLI
The CLI can be called by the commands described above. The CLI can take a couple optional arguments for configuring the reservoir anomaly calculation. These options are:

- -h, --help,                            show a help message and exit

- -o [output directory], --output-dir,   output directory to write the           reservoir anomalies file to, by default the file is written to './gww-anomalies/data'. Note that when using the Docker image it is not possible to set the output directory. If you wish to do that you can edit the volume binding in the docker compose file. 

- -r [reservoir id file], --reservoir_ids_file, text file containing reservoir FIDs. The FIDs should be on one line and seperated by a comma. WARNING if this file is not given the app will calculate reservoir anomalies for all reservoirs, this can take up to 7 hours or longer.

- -m [month] --month,                     the month to calculate the reservoir anomalies for in 'mm-dd-YYYY' format. By default the latest month is used.

- -v, --as-vector,                       write the anomalies file to a vector format (geoJSON). 