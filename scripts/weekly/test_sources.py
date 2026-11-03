import importlib.util,pathlib,unittest.mock as mock
spec=importlib.util.spec_from_file_location('prepare',pathlib.Path(__file__).with_name('prepare.py'));p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
with mock.patch.object(p.urllib.request,'urlopen',side_effect=TimeoutError('forced')) as call, mock.patch.object(p.time,'sleep'):
 assert p.fetch('https://fantasy.premierleague.com/api/test-timeout/',optional=True) is None
 assert call.call_count==3 and 'TimeoutError' in p.gaps[-1]
with mock.patch.object(p.urllib.request,'urlopen',side_effect=TimeoutError('forced')),mock.patch.object(p.time,'sleep'):
 try:p.fetch('https://fantasy.premierleague.com/api/test-timeout/');raise AssertionError('Essential timeout accepted')
 except RuntimeError:pass
assert p.match_id('Brighton & Hove Albion','Manchester United')=='26-27-prem-brighton-hove-albion-vs-manchester-united'
print('Source timeout tests passed: bounded three attempts, optional gap, essential failure, canonical team ID.')
