# bench-o-matic
Automate running browserbench.org benchmarks

Params:
* `-r,--runs`: Number of runs. i.e. `python3 bom.py --runs 100`
* `--full_speedometer2_score`: Collect full speedometer2 score or not (collect detailed score instead), default value set to True. i.e. `python3 bom.py --full_speedometer2_score=True`
* `--incognito`: Use incognito mode or not, default value set to False. i.e. `python3 bom.py --incognito=True`
* `--use_predefined_profile`: Use predefined profile or not, default value set to False. If not, the webdriver will create a new profile instead. i.e. `python3 bom.py --use_predefined_profile=True`
* `--sleep_interval`: Sleep interval between each pair of test, default value set to 30. i.e. `python3 bom.py --sleep_interval=60`
* `--use_randomized_finch_flag`: Use randomized finch flag or not, default value set to False. i.e. `python3 bom.py --use_randomized_finch_flag=True`
* `--max_wait_time`: Maximum wait time for a benchmark to finish.. i.e. `python3 bom.py --max_wait_time=1200`
* `--compare_stable_browsers`: Compare stable browsers or not, default value set to True. i.e. `python3 bom.py --compare_stable_browsers=True`

## MacOS
### Prequisites
Requires Python 3 native to the system CPU architecture (MacOS 12.3.1+ recommended).
Please also ensure Chrome browser and Safari browser are installed.

To use Chrome Canary, besides download the latest browser version via: https://www.google.com/chrome/canary/, you also need to download the chrome driver via: https://chromedriver.chromium.org/chromedriver-canary.

Safari's WebDriver support for developers is turned off by default. Need to enable safaridriver support (once)

```
sudo safaridriver --enable
```

### Python Environment

Python virtual environment is recommended. To set it up, open a terminal, changed to the `bench-o-matic` directory, then create the virtual environment:

```bash
python3 -m venv ./env
```

To activate the venv:

```bash
source ./env/bin/activate
```

Once the venv is activated, `python` should refer to `env/bin/python`. Then upgrade pip and install all dependencies.


```bash
python -m pip install --upgrade pip
python -m pip install --require-hashes -r requirements.txt
```

### Example sage
```bash
python bom.py
```

To deactivate venv:

```bash
deactivate
```

## Windows
We used the WMI module (https://pypi.org/project/WMI/) + Open Hardware Monitor (https://openhardwaremonitor.org/documentation/) (reference: https://stackoverflow.com/questions/3262603/accessing-cpu-temperature-in-python) to collect CPU temperature for Windows platfrom.
To install wmi: pip install wmi
To use Open Hardware Monior: download the software via https://openhardwaremonitor.org/downloads/.

Example usage: C:\Users\windo\Documents\GitHub\bench-o-matic>python bom.py --runs 2 --full_speedometer2_score=True --incognito=False --use_predefined_profile=True --sleep_interval=0 > log_test3.txt