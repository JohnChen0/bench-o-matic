#!/usr/bin/env python3
import logging
import os
import platform
import psutil
import random
import shutil
import subprocess
import time
from datetime import datetime
from selenium import webdriver
from time import monotonic


CHROME_PROFILE = "Profile 1"
CHROME_USER_DATA_DIR_MAC = r"/Users/chromecbb/Library/Application Support/Google/Chrome"
CHROME_CANARY_USER_DATA_DIR_MAC = r"/Users/chromecbb/Library/Application Support/Google/Chrome Canary"
CHROME_DEV_USER_DATA_DIR_MAC = r"/Users/chromecbb/Library/Application Support/Google/Chrome Dev"
CHROME_DRIVER_LOC_MAC = '/Users/chromecbb/Desktop/bench-o-matic/bench-o-matic/chromedriver'

CHROME_DRIVER_LOC_WIN = r'C:\Users\windo\Downloads\chromedriver_win32\chromedriver'
CHROME_USER_DATA_DIR_WIN = r"C:\Users\windo\AppData\Local\Google\Chrome\User Data" # for windows

EDGE_USER_DATA_DIR = r"C:\Users\windo\AppData\Local\Microsoft\Edge\User Data"
EDGE_PROFILE = "Profile 2"

class BenchOMatic():
    """Automate browserbench.org testing across browsers using webdriver"""
    def __init__(self, options):
        self.runs = options.runs
        self.full_speedometer2_score = options.full_speedometer2_score
        self.full_motionmark_score = options.full_motionmark_score
        self.full_jetstream_score = options.full_jetstream_score
        self.sleep_interval = options.sleep_interval
        self.max_wait_time = options.max_wait_time
        self.incognito = options.incognito
        self.use_predefined_profile = options.use_predefined_profile
        self.use_randomized_finch_flag = options.use_randomized_finch_flag
        self.use_enable_field_trial_config = options.use_enable_field_trial_config
        self.use_top_seeds = options.use_top_seeds
        self.compare_stable_browsers = options.compare_stable_browsers
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

        self.benchmarks = {
            'JetStream 2.1': {
                'url': 'https://browserbench.org/JetStream2.1/',
                'start': 'JetStream.start();',
                'done': "return (document.querySelectorAll('#result-summary>.score').length > 0);",
                'result': "return parseFloat(document.querySelector('#result-summary>.score').innerText);"
            }
        }

        if self.full_speedometer2_score:
            self.benchmarks['Speedometer 2.1'] = {
                'url': 'https://browserbench.org/Speedometer2.1/',
                'start': 'startTest();',
                'done': "return (document.getElementById('results-with-statistics') && document.getElementById('results-with-statistics').innerText.length > 0);",
                'result': "return parseInt(document.getElementById('result-number').innerText);"
            }
        else:
            self.benchmarks['Speedometer 2.1'] = {
                'url': 'https://browserbench.org/Speedometer2.1/',
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
            }
        if self.full_motionmark_score:
            self.benchmarks['MotionMark 1.2'] = {
                'url': 'https://browserbench.org/MotionMark1.2/',
                'start': 'benchmarkController.startBenchmark();',
                'done': "return (document.querySelector('#results>.body>.score-container>.score').innerText.length > 0);",
                'result': "return parseFloat(document.querySelector('#results>.body>.score-container>.score').innerText);"
            }
        else:
            self.benchmarks['MotionMark 1.2'] = {
                'url': 'https://browserbench.org/MotionMark1.2/',
                'start': 'benchmarkController.startBenchmark();',
                'done': "return (document.querySelector('#results>.body>.score-container>.score').innerText.length > 0);",
                'result': "return [parseFloat(document.querySelector('#results>.body>.score-container>.score').innerText), benchmarkRunnerClient.results._results.iterationsResults[0].testsResults.MotionMark];",
                'suites': [
                    'Multiply',
                    'Canvas Arcs',
                    'Leaves',
                    'Paths',
                    'Canvas Lines',
                    'Images',
                    'Design',
                    'Suits'
                ],
                'suite_result':
                    lambda results, suite: results[1][suite]['score']
            }

    def run(self):
        if self.full_speedometer2_score:
            print('Record speedometer2 score')
        else:
            print('Record detailed speedometer2 score')
        if self.full_motionmark_score:
            print('Record motionmark score')
        else:
            print('Record detailed motionmark score')
        if self.full_jetstream_score:
            print('Record jetstream score')
        else:
            print('Record detailed jetstream score')
        if self.use_predefined_profile:
            print('Use predefined user profile')
        if self.use_randomized_finch_flag:
            print('Use randomized finch flag')
        if self.use_enable_field_trial_config:
            print('Use enable field trial config')
        if self.use_top_seeds:
            print('Use top seeds')
        if self.incognito:
            print('Use incognito mode')
        if self.compare_stable_browsers:
            print('Compare stable browsers')
        else:
            print('Compare unstable browsers')

        """Run the requested tests"""
        benchmark_names = list(self.benchmarks.keys())
        browser_names = list(self.browsers.keys())

        # Initialize the CSV result files with a header
        for benchmark_name in benchmark_names:
            csv_file = self.bench_root + benchmark_name.replace(' ', '') + '.csv'
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

        for benchmark_name in benchmark_names:
            if 'Motion' in benchmark_name:
                print('Motion in: ' + benchmark_name)
                self.runs = 62
            run_orders = self.get_run_order(browser_names)
            print('Run order: {}'.format(run_orders))
            cur_runs = 0
            while cur_runs < self.runs:
                self.run_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print('')
                print('Run {}'.format(cur_runs + 1))
                results = {}
                self.current_benchmark = benchmark_name
                benchmark = self.benchmarks[benchmark_name]
                print('{}:'.format(benchmark_name))
                browsers = run_orders[cur_runs]
                print('browser run order {}'.format(browsers))
                time.sleep(self.sleep_interval)
                run_benchmark_successful = False
                if self.plat == "Windows":
                    temperature_before_test = self.get_current_temperature(before_testing=True)
                for name in browsers:
                    browser = self.browsers[name]
                    browser['name'] = name
                    self.current_browser = name
                    self.launch_browser(browser)
                    self.prepare_benchmark(benchmark)
                    run_benchmark_successful = self.run_benchmark(benchmark)
                    if run_benchmark_successful:
                        results[name] = self.collect_result(benchmark)
                    else:
                        logging.info('Benchmark failed')
                   # self.driver.close()
                    try:
                        self.driver.quit()
                    except Exception:
                        pass
                    # Kill Safari manually since it doesn't like to go away cleanly
                    if name == 'Safari':
                        subprocess.call(['killall', 'Safari'])
                    if not run_benchmark_successful:
                        break
                if not run_benchmark_successful:
                    continue
                if self.plat == "Windows":
                    temperature_after_test = self.get_current_temperature(before_testing=False)

                # Write the results for each run as they complete
                csv_file = self.bench_root + benchmark_name.replace(' ', '') + '.csv'
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
                cur_runs += 1
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
            # Use randomized finch flag
            # 1. Create a new folder as the --user-data-dir
            # 2. start chrome with special option:
            # options.add_experimental_option("excludeSwitches", ["disable-background-networking"])
            # 3. wait 10 seconds
            # 4. shut down chrome
            # 5. start chrome with the same user directory created in #1
            if self.use_randomized_finch_flag:
                cur_dir = os.getcwd()
                # Create an empty profile directory
                profile_dir = os.path.join(cur_dir, "Default")
                if os.path.exists(profile_dir):
                    shutil.rmtree(profile_dir, ignore_errors=True)
                os.makedirs(profile_dir)
                options.add_argument(r"--user-data-dir={}".format(profile_dir))
                options.add_experimental_option("excludeSwitches", ['disable-background-networking'])
                self.driver = self.get_chrome_driver(options, ver)
                time.sleep(10)
                self.driver.quit()
            elif self.use_predefined_profile:
                if self.plat == "Windows":
                    options.add_argument(r"--user-data-dir={}".format(CHROME_USER_DATA_DIR_WIN))
                else:
                    options.add_argument(r"--user-data-dir={}".format(CHROME_USER_DATA_DIR_MAC))
                options.add_argument(r"--profile-directory={}".format(CHROME_PROFILE))
            elif self.use_enable_field_trial_config:
                cur_dir = os.getcwd()
                # Create an empty profile directory
                profile_dir = os.path.join(cur_dir, "Default")
                if os.path.exists(profile_dir):
                    shutil.rmtree(profile_dir, ignore_errors=True)
                os.makedirs(profile_dir)
                options.add_argument(r"--user-data-dir={}".format(profile_dir))
                options.add_argument("--enable-field-trial-config")
                options.add_experimental_option("excludeSwitches", ['disable-background-networking'])
            elif self.use_top_seeds:
                cur_dir = os.getcwd()
                # Create an empty profile directory
                profile_dir = os.path.join(cur_dir, "Default")
                if os.path.exists(profile_dir):
                    shutil.rmtree(profile_dir, ignore_errors=True)
                os.makedirs(profile_dir)
                options.add_argument(r"--user-data-dir={}".format(profile_dir))
                options.add_experimental_option("excludeSwitches", ['disable-background-networking'])
                # The current top seeds are only for mac
                options.add_argument("--variations-test-seed-path=/Users/chromecbb/Desktop/bench-o-matic/bench-o-matic/mac_stable_variations_seed_with_default_groups.json")
                # options.add_argument("--variations-test-seed-path=/Users/chromecbb/Desktop/bench-o-matic/bench-o-matic/mac_stable_random_variations_seed.json")
            if self.compare_stable_browsers:
                self.driver = self.get_chrome_driver(options, ver)
            else:
                if self.plat == "Windows":
                    self.driver = webdriver.Chrome(options=options,
                        service=Service(CHROME_DRIVER_LOC_WIN))
                else:
                    self.driver = webdriver.Chrome(options=options,
                        service=Service(CHROME_DRIVER_LOC_MAC))
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
            ver = browser['vesion'] if 'version' in browser else 'latest'
            # Use randomized finch flag
            # 1. Create a new folder as the --user-data-dir
            # 2. start edge with special option:
            # options.add_experimental_option("excludeSwitches", ["disable-background-networking"])
            # 3. wait 10 seconds
            # 4. shut down chrome
            # 5. start edge with the same user directory created in #1
            if self.use_randomized_finch_flag:
                cur_dir = os.getcwd()
                # Create an empty profile directory
                profile_dir = os.path.join(cur_dir, "Default")
                if os.path.exists(profile_dir):
                    shutil.rmtree(profile_dir, ignore_errors=True)
                os.makedirs(profile_dir)
                options.add_argument(r"--user-data-dir={}".format(profile_dir))
                options.add_experimental_option("excludeSwitches", ['disable-background-networking'])
                #self.driver = webdriver.Edge(options=options,
                #                             service=Service(EdgeChromiumDriverManager(version=ver).install()))
                self.driver = webdriver.Edge(options=options, service=Service(r'C:\Users\windo\Downloads\edgedriver_win64\msedgedriver'))
                time.sleep(10)
                self.driver.quit()
            elif self.use_predefined_profile:
                options.add_argument(r"--user-data-dir={}".format(EDGE_USER_DATA_DIR))
                options.add_argument(r"--profile-directory={}".format(EDGE_PROFILE))
            #self.driver = webdriver.Edge(options=options,
            #                             service=Service(EdgeChromiumDriverManager(version=ver).install()))
            self.driver = webdriver.Edge(options=options, service=Service(r'C:\Users\windo\Downloads\edgedriver_win64\msedgedriver'))
        elif browser['type'] == 'Safari':
            if 'driver' in browser:
                from selenium.webdriver.safari.options import Options
                from selenium.webdriver.safari.service import Service
                options = Options()
                options.use_technology_preview = True
                capabilities = webdriver.DesiredCapabilities.SAFARI.copy()
                capabilities['browserName'] = "Safari Technology Preview"
                self.driver = webdriver.Safari(desired_capabilities=capabilities, options=options, service=Service(executable_path='/Applications/Safari Technology Preview.app/Contents/MacOS/safaridriver'))
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

    def get_chrome_driver(self, options, ver):
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        """Get ready to run the given benchmark"""
        try:
            driver = webdriver.Chrome(options=options,
                service=Service(ChromeDriverManager(version=ver).install()))
        except:
            # For Chrome Canary, download the latest chrome driver via: https://chromedriver.chromium.org/chromedriver-canary,
            # and use the location for the Service(...) input.
            # For Chrome Dev, download the latest chrome driver based on: https://chromedriver.chromium.org/downloads/version-selection
            if self.plat == "Windows":
                driver = webdriver.Chrome(options=options,
                    service=Service(CHROME_DRIVER_LOC_WIN))
            else:
                driver = webdriver.Chrome(options=options,
                    service=Service(CHROME_DRIVER_LOC_MAC))
        return driver

    def prepare_benchmark(self, benchmark):
        """Get ready to run the given benchmark"""
        self.driver.get(benchmark['url'])
        self.wait_for_idle()

    def run_benchmark(self, benchmark):
        """Run the benchmark and wait for it to finish"""
        logging.info('Starting benchmark...')
        if 'Jet' in benchmark['url']:
            time.sleep(60)
        else:
            time.sleep(5)
        self.driver.execute_script(benchmark['start'])

        # Wait up to an hour for the benchmark to run
        done = False
        end_time = monotonic() + self.max_wait_time
        while not done and monotonic() < end_time:
            try:
                time.sleep(2)
                result = self.driver.execute_script(benchmark['done'])
                if result:
                    done = True
            except Exception:
                logging.exception('Error checking benchmark status')
        return done
        
    def get_run_order(self, browser_keys):
        if len(browser_keys) != 2:
            raise Exception('Expect two browsers for the paired testing, but got {}'.format(len(browser_keys)))
        # Runs that chrome will go first
        chrome_first_runs = random.sample(range(2, self.runs), int((self.runs-2)/2))
        chrome_first_runs.append(0)
        run_orders = []
        for order in range(0, self.runs):
            if order in chrome_first_runs:
                run_order = self.get_chrome_run_first(browser_keys)
            else:
                run_order = self.get_chrome_run_last(browser_keys)
            run_orders.append(run_order)
        return run_orders
        
    def get_chrome_run_first(self, browser_keys):
        run_order = []
        for key in browser_keys:
            if 'Chrome' in key:
                run_order.append(key)
        for key in browser_keys:
            if 'Chrome' not in key:
                run_order.append(key)
        return run_order
    
    def get_chrome_run_last(self, browser_keys):
        run_order = []
        for key in browser_keys:
            if 'Chrome' not in key:
                run_order.append(key)
        for key in browser_keys:
            if 'Chrome' in key:
                run_order.append(key)
        return run_order
            
    def collect_result(self, benchmark):
        """Collect the benchmark result"""
        result = ''
        try:
            result = self.driver.execute_script(benchmark['result'])
        except Exception:
            pass
        print('    {}: {}'.format(self.current_browser, result[0] if isinstance(result, list) else result))

        # Save the screnshot
        file_path = self.bench_root + '{}-{}-{}.png'.format(self.current_benchmark.replace(' ', ''), self.current_browser, self.run_timestamp.replace(':', '').replace(' ', ''))
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
            if self.compare_stable_browsers:
                browsers = self.detect_browser('Google Chrome', 'Chrome', 'Chrome', browsers)
                browsers = self.detect_browser('Safari', 'Safari', 'Safari', browsers)
            else:
                browsers = self.detect_browser('Google Chrome Dev', 'Chrome Dev', 'Chrome', browsers)
                browsers = self.detect_browser('Safari Technology Preview', 'Safari Technology Preview', 'Safari', browsers)

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
                        #if name.startswith('Chrome'):
                        #    build = re.search(r'^([\d.][\d.][\d])', browser_version).group(1)
                        #    latest = requests.get('https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{}'.format(build)).text
                        #    if latest:
                        #        browser['version'] = latest
                                # Get the version up to the build and fetch the latest matching Chromedriver build
                        #else:
                        browser['version'] = browser_version

        logging.info('Detected Browsers:')
        for browser in browsers:
            logging.info('%s: %s', browser, browsers[browser]['exe'])
        self.browsers = browsers

    def detect_browser(self, app_name, browser_name, browser_type, browsers):
        browser_path = '/Applications/{}.app/Contents/MacOS/{}'.format(app_name, app_name)
        if browser_name not in browsers and os.path.isfile(browser_path):
            if browser_name != 'Safari Technology Preview':
                browsers[browser_name] = {'exe': browser_path, 'type': browser_type}
            else:
                browsers[browser_name] = {'exe': browser_path, 'type': browser_type, 'driver': '/Applications/Safari Technology Preview.app/Contents/MacOS/safaridriver'}
        else:
            logging.error('{} does not exist, please install it and put it in the following path: {}'.format(browser_name, browser_path))
        return browsers


if '__main__' == __name__:
    import argparse
    parser = argparse.ArgumentParser(description='Bench-o-matic', prog='bom')
    parser.add_argument('-v', '--verbose', action='count',
                        help="Increase verbosity (specify multiple times for more). -vvvv for full debug output.")
    parser.add_argument('-r', '--runs', type=int, default=1, help='Number of runs.')
    parser.add_argument('--full_speedometer2_score', default=True, type=lambda x: (str(x).lower() == 'true'))
    parser.add_argument('--full_motionmark_score', default=True, type=lambda x: (str(x).lower() == 'true'))
    parser.add_argument('--full_jetstream_score', default=True, type=lambda x: (str(x).lower() == 'true'))
    parser.add_argument('--incognito', default=False, type=lambda x: (str(x).lower() == 'true'))
    parser.add_argument('--use_predefined_profile', default=False, type=lambda x: (str(x).lower() == 'true'))
    parser.add_argument('--use_randomized_finch_flag', default=False, type=lambda x: (str(x).lower() == 'true'))
    parser.add_argument('--use_enable_field_trial_config', default=False, type=lambda x: (str(x).lower() == 'true'))
    parser.add_argument('--use_top_seeds', default=False, type=lambda x: (str(x).lower() == 'true'))
    parser.add_argument('--sleep_interval', type=int, default=30, help='Time.sleep() interval between pair of runs.')
    parser.add_argument('--max_wait_time', type=int, default=1200, help='Maximum wait time for a benchmark to finish.')
    parser.add_argument('--compare_stable_browsers', default=True, type=lambda x: (str(x).lower() == 'true'))
    options = parser.parse_args()

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
