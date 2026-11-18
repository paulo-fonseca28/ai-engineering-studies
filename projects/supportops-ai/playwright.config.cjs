const {defineConfig} = require('@playwright/test');
module.exports = defineConfig({
  testDir:'./tests/browser', workers:1, retries:0, timeout:180000,
  use:{launchOptions:{slowMo:Number(process.env.DEMO_SLOW_MO || 0)},baseURL:'http://127.0.0.1:8765', viewport:{width:1440,height:1100}, video:'on', screenshot:'only-on-failure', trace:'retain-on-failure'},
  webServer:{command:'.venv/bin/python scripts/browser_server.py',url:'http://127.0.0.1:8765/health',reuseExistingServer:false,timeout:30000},
  reporter:[['list'],['json',{outputFile:'test-results/browser-results.json'}]]
});
