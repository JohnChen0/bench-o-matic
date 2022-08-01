#!/usr/bin/env python3
import logging
import os
import platform
import psutil
import random
import subprocess
import time
from datetime import datetime
from selenium import webdriver
from time import monotonic

class BenchOMatic():
    """Automate browserbench.org testing across browsers using webdriver"""
    def __init__(self, options):
        self.runs = options.runs
        self.full_speedometer2_score = options.full_speedometer2_score
        self.sleep_interval = options.sleep_interval
        self.incognito = options.incognito
        self.use_predefined_profile = options.use_predefined_profile
        self.driver = None
        self.detect_browsers()
        self.current_browser = None
        self.current_benchmark = None
        self.root_path = os.path.abspath(os.path.dirname(__file__))
        self.bench_root = os.path.join(self.root_path, datetime.now().strftime('%Y%m%d-%H%M%S-'))
        self.run_timestamp = None
        self.plat = platform.system()
        if self.plat == "Windows":
            import wmi
            self.w = wmi.WMI(namespace="root\OpenHardwareMonitor")
        if self.full_speedometer2_score == True:
            self.benchmarks = {
                'Speedometer 2.0': {
                    'url': 'https://browserbench.org/Speedometer2.0/',
                    'start': 'startTest();',
                    'done': "return (document.getElementById('results-with-statistics') && document.getElementById('results-with-statistics').innerText.length > 0);",
                    'result': "return parseInt(document.getElementById('result-number').innerText);"
                },
                'MotionMark 1.2': {
                    'url': 'https://browserbench.org/MotionMark1.2/',
                    'start': 'benchmarkController.startBenchmark();',
                    'done': "return (document.querySelector('#results>.body>.score-container>.score').innerText.length > 0);",
                    'result': "return parseFloat(document.querySelector('#results>.body>.score-container>.score').innerText);"
                },
                'JetStream 2': {
                    'url': 'https://browserbench.org/JetStream/',
                    'start': 'JetStream.start();',
                    'done': "return (document.querySelectorAll('#result-summary>.score').length > 0);",
                    'result': "return parseFloat(document.querySelector('#result-summary>.score').innerText);"
                }
            }
        else:
            self.benchmarks = {
                'Speedometer 2.0': {
                    'url': 'https://browserbench.org/Speedometer2.0/',
                    'start': 'startTest();',
                    'done': "return (document.getElementById('results-with-statistics') && document.getElementById('results-with-statistics').innerText.length > 0);",
                    'result': "return [parseInt(document.getElementById('result-number').innerText), benchmarkClient._measuredValuesList];",
                    'suites': [
                        'Angular2-TypeScript-TodoMVC',
                        'AngularJS-TodoMVC',
                        'BackboneJS-TodoMVC',
                        'Elm-TodoMVC',
                        'EmberJS-Debug-TodoMVC',
                        'EmberJS-TodoMVC',
                        'Flight-TodoMVC',
                        'Inferno-TodoMVC',
                        'Preact-TodoMVC',
                        'React-Redux-TodoMVC',
                        'React-TodoMVC',
                        'Vanilla-ES2015-Babel-Webpack-TodoMVC',
                        'Vanilla-ES2015-TodoMVC',
                        'VanillaJS-TodoMVC',
                        'VueJS-TodoMVC',
                        'jQuery-TodoMVC',
                    ],
                    'suite_result':
                        lambda results, suite: sum([20000 / r['tests'][suite]['total'] for r in results[1]]) / len(results[1]),
                },
                'MotionMark 1.2': {
                    'url': 'https://browserbench.org/MotionMark1.2/',
                    'start': 'benchmarkController.startBenchmark();',
                    'done': "return (document.querySelector('#results>.body>.score-container>.score').innerText.length > 0);",
                    'result': "return parseFloat(document.querySelector('#results>.body>.score-container>.score').innerText);"
                },
                'JetStream 2': {
                    'url': 'https://browserbench.org/JetStream/',
                    'start': 'JetStream.start();',
                    'done': "return (document.querySelectorAll('#result-summary>.score').length > 0);",
                    'result': "return parseFloat(document.querySelector('#result-summary>.score').innerText);"
                }
            }

    def run(self):
        """Run the requested tests"""
        benchmark_names = list(self.benchmarks.keys())
        browser_names = list(self.browsers.keys())

        # Initialize the CSV result files with a header
        for benchmark_name in benchmark_names:
            csv_file = self.bench_root + benchmark_name.replace(' ', '') + '.csv'
            if self.full_speedometer2_score == False:
                with open(csv_file, 'wt') as f:
                    f.write('Run')
                    display_names = []
                    for browser_name in browser_names:
                        if 'version' in self.browsers[browser_name]:
                            browser_name += ' ' + self.browsers[browser_name]['version']
                        display_names.append(browser_name)
                        f.write(',{}'.format(browser_name))
                    if 'suites' in self.benchmarks[benchmark_name]:
                        for suite in self.benchmarks[benchmark_name]['suites']:
                            for browser_name in display_names:
                                f.write(',{} {}'.format(browser_name, suite))
                    f.write(',temp_before_test, temp_after_test')
                    f.write('\n')
            else:
                with open(csv_file, 'wt') as f:
                    f.write('Run')
                    for browser_name in browser_names:
                        if 'version' in self.browsers[browser_name]:
                            browser_name += ' ' + self.browsers[browser_name]['version']
                        f.write(',{}'.format(browser_name))
                    f.write(',temp_before_test, temp_after_test')
                    f.write('\n')

        
        benchmarks = list(self.benchmarks.keys())
        for benchmark_name in benchmarks:
            for run in range(self.runs):
                self.run_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print('')
                print('Run {}'.format(run + 1))
                results = {}
                self.current_benchmark = benchmark_name
                benchmark = self.benchmarks[benchmark_name]
                print('{}:'.format(benchmark_name))
                browsers = list(self.browsers.keys())
                random.shuffle(browsers)
                time.sleep(self.sleep_interval)
                if self.plat == "Windows":
                    temperature_before_test = self.get_current_temperature(before_testing=True)
                for name in browsers:
                    browser = self.browsers[name]
                    browser['name'] = name
                    self.current_browser = name
                    self.launch_browser(browser)
                    self.prepare_benchmark(benchmark)
                    if self.run_benchmark(benchmark):
                        results[name] = self.collect_result(benchmark)
                    else:
                        logging.info('Benchmark failed')
                    self.driver.close()
                    try:
                        self.driver.quit()
                    except Exception:
                        pass
                    # Kill Safari manually since it doesn't like to go away cleanly
                    if name == 'Safari':
                        subprocess.call(['killall', 'Safari'])
                if self.plat == "Windows":
                    temperature_after_test = self.get_current_temperature(before_testing=False)

                # Write the results for each run as they complete
                csv_file = self.bench_root + benchmark_name.replace(' ', '') + '.csv'
                if self.full_speedometer2_score == False:
                    with open(csv_file, 'at') as f:
                        f.write(self.run_timestamp)
                        for browser_name in browser_names:
                            result = results[browser_name] if browser_name in results else ''
                            f.write(',{}'.format(result[0] if isinstance(result, list) else result))
                        if 'suites' in benchmark:
                            for suite in benchmark['suites']:
                                for browser_name in browser_names:
                                    if browser_name in results:
                                        f.write(',{}'.format(benchmark['suite_result'](results[browser_name], suite)))
                                    else:
                                        f.write(',')
                        if self.plat == "Windows":
                            f.write(',{}, {}'.format(temperature_before_test, temperature_after_test))
                        f.write('\n')
                else:
                    with open(csv_file, 'at') as f:
                        f.write(self.run_timestamp)
                        for browser_name in browser_names:
                            f.write(',{}'.format(results[browser_name] if browser_name in results else ''))
                        if self.plat == "Windows":
                            f.write(',{}, {}'.format(temperature_before_test, temperature_after_test))
                        f.write('\n')
            time.sleep(1200)

    def launch_browser(self, browser):
        """Launch the selected browser"""
        logging.info('Launching {}...'.format(browser['name']))
        plat = platform.system()
        if browser['type'] == 'Chrome':
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            os.environ['WDM_LOG'] = '0'
            options = Options()
            # incognito mode
            if self.incognito:
                options.add_argument("--incognito")
            options.binary_location = browser['exe']
            ver = 'latest'
            ver = browser['version'] if 'version' in browser else 'latest'
            # Use specific chrome profile, ref link: https://stackoverflow.com/questions/52394408/how-to-use-chrome-profile-in-selenium-webdriver-python-3
            # 1. Create a new profile via chrome browser
            # 2. type chrome://version, check the path of the new profile
            # 3. set the profile path
            if self.use_predefined_profile:
                options.add_argument(r"--user-data-dir=C:\Users\windo\AppData\Local\Google\Chrome\User Data") #e.g. C:\Users\You\AppData\Local\Google\Chrome\User Data
                options.add_argument(r"--profile-directory=Profile 1") #e.g. Profile 1
            self.driver = webdriver.Chrome(options=options, service=Service(ChromeDriverManager(version=ver).install()))
            if plat == "Darwin":
                self.driver.execute_cdp_cmd(
                    'Runtime.setMaxCallStackSizeToCapture',
                     dict(size=0))
        elif browser['type'] == 'Edge':
            from selenium.webdriver.edge.options import Options
            from selenium.webdriver.edge.service import Service
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            os.environ['WDM_LOG'] = '0'
            options = Options()
            # incognito mode
            if self.incognito:
                options.add_argument("-inprivate")
            options.binary_location = browser['exe']
            ver = 'latest'
            ver = browser['vesion'] if 'version' in browser else 'latest'
            # Use specific edge profile
            # 1. Create a new profile via edge browser
            # 2. type edge://version, check the path of the new profile
            # 3. set the profile path
            if self.use_predefined_profile:
                options.add_argument(r"--user-data-dir=C:\Users\windo\AppData\Local\Microsoft\Edge\User Data")
                options.add_argument(r"--profile-directory=Profile 2")
            self.driver = webdriver.Edge(options = options, service=Service(EdgeChromiumDriverManager(version=ver).install()))
        elif browser['type'] == 'Safari':
            if 'driver' in browser:
                from selenium.webdriver.safari.options import Options
                options = Options()
                options.binary_location = browser['exe']
                options.use_technology_preview = True
                self.driver = webdriver.Safari(options=options)
            else:
                self.driver = webdriver.Safari()
        elif browser['type'] == 'Firefox':
            from selenium.webdriver.firefox.options import Options
            from selenium.webdriver.firefox.service import Service
            from webdriver_manager.firefox import GeckoDriverManager
            os.environ['WDM_LOG'] = '0'
            options = Options()
            options.binary_location = browser['exe']
            #ver = browser['version'] if 'version' in browser else 'latest'
            ver = 'latest'
            self.driver = webdriver.Firefox(options=options, service=Service(GeckoDriverManager(version=ver).install()))
        self.driver.set_page_load_timeout(600)
        self.driver.set_script_timeout(30)

        # Get the browser version
        if 'version' in self.driver.capabilities:
            self.current_browser += ' ' + self.driver.capabilities['version']
        elif 'browserVersion' in self.driver.capabilities:
            self.current_browser += ' ' + self.driver.capabilities['browserVersion']

        # Make sure all browsers use the same window size
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1440, 900)

    def prepare_benchmark(self, benchmark):
        """Get ready to run the given benchmark"""
        self.driver.get(benchmark['url'])
        self.wait_for_idle()

    def run_benchmark(self, benchmark):
        """Run the benchmark and wait for it to finish"""
        logging.info('Starting benchmark...')
        self.driver.execute_script(benchmark['start'])

        # Wait up to an hour for the benchmark to run
        done = False
        end_time = monotonic() + 3600
        while not done and monotonic() < end_time:
            try:
                time.sleep(2)
                result = self.driver.execute_script(benchmark['done'])
                if result:
                    done = True
            except Exception:
                logging.exception('Error checking benchmark status')
        return done
    
    def collect_result(self, benchmark):
        """Collect the benchmark result"""
        result = ''
        try:
            result = self.driver.execute_script(benchmark['result'])
        except Exception:
            pass
        print('    {}: {}'.format(self.current_browser, result[0] if isinstance(result, list) else result))

        # Save the screnshot
        file_path = self.bench_root + '{}-{}.png'.format(self.current_benchmark.replace(' ', ''), self.current_browser)
        self.driver.get_screenshot_as_file(file_path)

        return result
 
    def get_current_temperature(self, before_testing=False):
        temperature_infos = self.w.Sensor()
        for sensor in temperature_infos:
            if sensor.SensorType==u'Temperature':
                if "Package" in sensor.Name:
                    # print(sensor.Name)
                    return sensor.Value
        return "temp not available"
  
    def wait_for_idle(self, timeout=30):
        """Wait for the system to go idle for at least 2 seconds"""
        logging.info("Waiting for Idle...")
        cpu_count = psutil.cpu_count()
        if cpu_count > 0:
            # No single core more than 30% or 10% total, whichever is higher
            target_pct = max(30. / float(cpu_count), 10.)
            idle_start = None
            end_time = monotonic() + timeout
            last_update = monotonic()
            idle = False
            while not idle and monotonic() < end_time:
                check_start = monotonic()
                pct = psutil.cpu_percent(interval=0.5)
                if pct <= target_pct:
                    if idle_start is None:
                        idle_start = check_start
                    if monotonic() - idle_start > 2:
                        idle = True
                else:
                    idle_start = None
                if not idle and monotonic() - last_update > 1:
                    last_update = monotonic()
                    logging.info("CPU Utilization: %0.1f%% (%d CPU's, %0.1f%% target)", pct, cpu_count, target_pct)

    def detect_browsers(self):
        """Find the various known-browsers in case they are not explicitly configured (ported from WebPageTest)"""
        browsers = {}
        plat = platform.system()
        if plat == "Windows":
            local_appdata = os.getenv('LOCALAPPDATA')
            program_files = str(os.getenv('ProgramFiles'))
            program_files_x86 = str(os.getenv('ProgramFiles(x86)'))
            # Allow 32-bit python to detect 64-bit browser installs
            if program_files == program_files_x86 and program_files.find(' (x86)') >= 0:
                program_files = program_files.replace(' (x86)', '')
            # Chrome
            paths = [program_files, program_files_x86, local_appdata]
            channels = ['Chrome', 'Chrome Beta']
            for channel in channels:
                for path in paths:
                    if path is not None and channel not in browsers:
                        chrome_path = os.path.join(path, 'Google', channel,
                                                'Application', 'chrome.exe')
                        if os.path.isfile(chrome_path):
                            browsers[channel] = {'exe': chrome_path, 'type': 'Chrome'}
            # Firefox browsers
            paths = [program_files, program_files_x86]
            for path in paths:
                if path is not None and 'Firefox' not in browsers:
                    firefox_path = os.path.join(path, 'Mozilla Firefox', 'firefox.exe')
                    if os.path.isfile(firefox_path):
                        browsers['Firefox'] = {'exe': firefox_path, 'type': 'Firefox'}
                if path is not None and 'Firefox' not in browsers:
                    firefox_path = os.path.join(path, 'Firefox', 'firefox.exe')
                    if os.path.isfile(firefox_path):
                        browsers['Firefox'] = {'exe': firefox_path, 'type': 'Firefox'}
                if path is not None and 'Firefox ESR' not in browsers:
                    firefox_path = os.path.join(path, 'Mozilla Firefox ESR', 'firefox.exe')
                    if os.path.isfile(firefox_path):
                        browsers['Firefox ESR'] = {'exe': firefox_path, 'type': 'Firefox'}
                if path is not None and 'Firefox Beta' not in browsers:
                    firefox_path = os.path.join(path, 'Mozilla Firefox Beta', 'firefox.exe')
                    if os.path.isfile(firefox_path):
                        browsers['Firefox Beta'] = {'exe': firefox_path, 'type': 'Firefox'}
                if path is not None and 'Firefox Beta' not in browsers:
                    firefox_path = os.path.join(path, 'Firefox Beta', 'firefox.exe')
                    if os.path.isfile(firefox_path):
                        browsers['Firefox Beta'] = {'exe': firefox_path, 'type': 'Firefox'}
            # Microsoft Edge (Chromium)
            paths = [program_files, program_files_x86, local_appdata]
            channels = ['Edge', 'Edge Dev']
            for channel in channels:
                for path in paths:
                    edge_path = os.path.join(path, 'Microsoft', channel, 'Application', 'msedge.exe')
                    if os.path.isfile(edge_path):
                        browser_name = 'Microsoft {0} (Chromium)'.format(channel)
                        if browser_name not in browsers:
                            browsers[browser_name] = {'exe': edge_path, 'type': 'Edge'}
            if local_appdata is not None:
                edge_path = os.path.join(local_appdata, 'Microsoft', 'Edge SxS', 'Application', 'msedge.exe')
                if os.path.isfile(edge_path):
                    browsers['Microsoft Edge Canary (Chromium)'] = {'exe': edge_path, 'type': 'Edge'}
            # Brave
            paths = [program_files, program_files_x86]
            for path in paths:
                if path is not None and 'Brave' not in browsers:
                    brave_path = os.path.join(path, 'BraveSoftware', 'Brave-Browser', 'Application', 'brave.exe')
                    if os.path.isfile(brave_path):
                        browsers['Brave'] = {'exe': brave_path, 'type': 'Chrome'}
        elif plat == "Linux":
            chrome_path = '/opt/google/chrome/chrome'
            if 'Chrome' not in browsers and os.path.isfile(chrome_path):
                browsers['Chrome'] = {'exe': chrome_path, 'type': 'Chrome'}
            beta_path = '/opt/google/chrome-beta/chrome'
            if 'Chrome Beta' not in browsers and os.path.isfile(beta_path):
                browsers['Chrome Beta'] = {'exe': beta_path, 'type': 'Chrome'}
            # Firefox browsers
            firefox_path = '/usr/lib/firefox/firefox'
            if 'Firefox' not in browsers and os.path.isfile(firefox_path):
                browsers['Firefox'] = {'exe': firefox_path, 'type': 'Firefox'}
            firefox_path = '/usr/bin/firefox'
            if 'Firefox' not in browsers and os.path.isfile(firefox_path):
                browsers['Firefox'] = {'exe': firefox_path, 'type': 'Firefox'}
            firefox_path = '/usr/lib/firefox-esr/firefox-esr'
            if 'Firefox ESR' not in browsers and os.path.isfile(firefox_path):
                browsers['Firefox ESR'] = {'exe': firefox_path, 'type': 'Firefox'}
            # Brave
            brave_path = '/opt/brave.com/brave/brave-browser'
            if 'Brave' not in browsers and os.path.isfile(brave_path):
                browsers['Brave'] = {'exe': brave_path, 'type': 'Chrome'}
            # Microsoft Edge
            edge_path = '/usr/bin/microsoft-edge-stable'
            if os.path.isfile(edge_path):
                if 'Microsoft Edge' not in browsers:
                    browsers['Microsoft Edge'] = {'exe': edge_path, 'type': 'Chrome'}
            edge_path = '/usr/bin/microsoft-edge-beta'
            if os.path.isfile(edge_path):
                if 'Microsoft Edge Beta' not in browsers:
                    browsers['Microsoft Edge Beta'] = {'exe': edge_path, 'type': 'Chrome'}
            edge_path = '/usr/bin/microsoft-edge-dev'
            if os.path.isfile(edge_path):
                if 'Microsoft Edge Dev' not in browsers:
                    browsers['Microsoft Edge Dev'] = {'exe': edge_path, 'type': 'Chrome'}

        elif plat == "Darwin":
            chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            if 'Chrome' not in browsers and os.path.isfile(chrome_path):
                browsers['Chrome'] = {'exe': chrome_path, 'type': 'Chrome'}
            chrome_path = '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta'
            if 'Chrome Beta' not in browsers and os.path.isfile(chrome_path):
                browsers['Chrome Beta'] = {'exe': chrome_path, 'type': 'Chrome'}
            firefox_path = '/Applications/Firefox.app/Contents/MacOS/firefox'
            if 'Firefox' not in browsers and os.path.isfile(firefox_path):
                browsers['Firefox'] = {'exe': firefox_path, 'type': 'Firefox'}
            safari_path = '/Applications/Safari.app/Contents/MacOS/Safari'
            if 'Safari' not in browsers and os.path.isfile(safari_path):
                browsers['Safari'] = {'exe': safari_path, 'type': 'Safari'}
            """
            safari_path = '/Applications/Safari Technology Preview.app/Contents/MacOS/Safari Technology Preview'
            if 'Safari Technology Preview' not in browsers and os.path.isfile(safari_path):
                browsers['Safari Technology Preview'] = {'exe': safari_path, 'type': 'Safari',
                    'driver': '/Applications/Safari Technology Preview.app/Contents/MacOS/safaridriver'}
            """
            # Get the version of each
            import plistlib
            import re
            import requests
            for name in browsers:
                browser = browsers[name]
                plist_file = os.path.join(os.path.dirname(os.path.dirname(browser['exe'])), 'Info.plist')
                if os.path.isfile(plist_file):
                    with open(plist_file, 'rb') as f:
                        browser_version = plistlib.load(f)['CFBundleShortVersionString']
                        if name.startswith('Chrome'):
                            build = re.search(r'^([\d.][\d.][\d])', browser_version).group(1)
                            latest = requests.get('https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{}'.format(build)).text
                            if latest:
                                browser['version'] = latest
                                # Get the version up to the build and fetch the latest matching Chromedriver build
                        else:
                            browser['version'] = browser_version

        logging.info('Detected Browsers:')
        for browser in browsers:
            logging.info('%s: %s', browser, browsers[browser]['exe'])
        self.browsers = browsers

if '__main__' == __name__:
    import argparse
    parser = argparse.ArgumentParser(description='Bench-o-matic', prog='bom')
    parser.add_argument('-v', '--verbose', action='count',
                        help="Increase verbosity (specify multiple times for more). -vvvv for full debug output.")
    parser.add_argument('-r', '--runs', type=int, default=1, help='Number of runs.')
    parser.add_argument('--full_speedometer2_score', default=True, type=lambda x: (str(x).lower() == 'true'))
    parser.add_argument('--incognito', default=False, type=lambda x: (str(x).lower() == 'true'))
    parser.add_argument('--use_predefined_profile', default=False, type=lambda x: (str(x).lower() == 'true'))
    parser.add_argument('--sleep_interval', type=int, default=30, help='Time.sleep() interval between pair of runs.')
    options, _ = parser.parse_known_args()

    # Set up logging
    log_level = logging.CRITICAL
    if options.verbose is not None:
      if options.verbose == 1:
          log_level = logging.ERROR
      elif options.verbose == 2:
          log_level = logging.WARNING
      elif options.verbose == 3:
          log_level = logging.INFO
      elif options.verbose >= 4:
          log_level = logging.DEBUG
    logging.basicConfig(
        level=log_level, format="%(asctime)s.%(msecs)03d - %(message)s", datefmt="%H:%M:%S")

    # Keep the display awake (macos)
    if platform.system() == "Darwin":
        subprocess.Popen(['caffeinate', '-dis'])

    # Kick off the actual benchmarking
    bom = BenchOMatic(options)
    bom.run()
