# bench-o-matic
Automate running browserbench.org benchmarks

Params:
* `-r,--runs`: Number of runs. i.e. `python3 bom.py --runs 100`
* `--full_speedometer2_score`: Collect full speedometer2 score or not (collect detailed score instead), default value set to True. i.e. `python3 bom.py --full_speedometer2_score=True`
* `--incognito`: Use incognito mode or not, default value set to False. i.e. `python3 bom.py --incognito=True`
* `--use_predefined_profile`: Use predefined profile or not, default value set to False. If not, the webdriver will create a new profile instead. i.e. `python3 bom.py --use_predefined_profile=True`
* `--sleep_interval`: Sleep interval between each pair of test, default value set to 30. i.e. `python3 bom.py --sleep_interval=60`

## MacOS
Requires Python 3 native to the system CPU architecture (MacOS 12.3.1+ recommended).

```bash
python3 -m pip install --upgrade pip
python3 -m pip install selenium psutil webdriver-manager requests
```

Also need to enable safaridriver support (once)
```
sudo safaridriver --enable
```

## Windows
We used the WMI module (https://pypi.org/project/WMI/) + Open Hardware Monitor (https://openhardwaremonitor.org/documentation/) (reference: https://stackoverflow.com/questions/3262603/accessing-cpu-temperature-in-python) to collect CPU temperature for Windows platfrom.
To install wmi: pip install wmi
To use Open Hardware Monior: download the software via https://openhardwaremonitor.org/downloads/.

Example usage: C:\Users\windo\Documents\GitHub\bench-o-matic>python bom.py --runs 2 --full_speedometer2_score=True --incognito=False --use_predefined_profile=True --sleep_interval=0 > log_test3.txt