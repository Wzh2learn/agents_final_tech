"""CPU-only qualification contracts; all container and helper actions are fake."""
from contextlib import contextmanager
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'research/agent_frontier_portfolio_20261029/qualify_contextbench_pool.py'
spec=importlib.util.spec_from_file_location('contextbench_pool_contract',SCRIPT)
r=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=r
spec.loader.exec_module(r)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf8')
    return sha(path)


class MappedLabelTests(unittest.TestCase):
    def test_django_published_nodes_map_to_exact_labels(self):
        labels=['tests/aggregation/tests.py::AggregateTests::test_sum',
                'tests/aggregation/tests.py::AggregateTests::test_count']
        self.assertEqual(r.mapped_labels('django/django',labels),
                         ['aggregation.tests.AggregateTests.test_sum',
                          'aggregation.tests.AggregateTests.test_count'])

    def test_sympy_nodes_are_preserved_in_order(self):
        labels=['sympy/core/tests/test_basic.py::test_has',
                'sympy/core/tests/test_basic.py::test_subs']
        before=list(labels)
        self.assertEqual(r.mapped_labels('sympy/sympy',labels),before)
        self.assertEqual(labels,before)

    def test_duplicates_escapes_and_unmapped_labels_are_rejected(self):
        invalid=[('django/django',['tests/app/tests.py::Case::test_a']*2),
                 ('sympy/sympy',['sympy/core/tests/test_basic.py::test_has']*2),
                 ('django/django',['../tests/app/tests.py::Case::test_a']),
                 ('sympy/sympy',['/tmp/test_unsafe.py::test_a']),
                 ('sympy/sympy',['sympy/../tests/test_a.py::test_a']),
                 ('django/django',['not a runnable published label']),
                 ('sympy/sympy',['not_a_test_node']),('unknown',['test_a'])]
        for repo,labels in invalid:
            with self.subTest(repo=repo,labels=labels),self.assertRaises(ValueError):
                r.mapped_labels(repo,labels)


def reference(path,value):
    return {'path':str(path),'sha256':write(path,value)}


def archive(path,repo,revision):
    prefix=repo.split('/')[1]+'-'+revision
    with tarfile.open(path,'w:gz') as stream:
        info=tarfile.TarInfo(prefix+'/LICENSE');payload=b'OWNED_FAKE_LICENSE\n';info.size=len(payload)
        stream.addfile(info,io.BytesIO(payload))
        if repo=='django/django':
            for i in range(4):
                link=tarfile.TarInfo(prefix+'/docs/_theme/djangodocs-epub/static/link'+str(i))
                link.type=tarfile.SYMTYPE;link.linkname='../../djangodocs/static/fake'+str(i)
                stream.addfile(link)


@contextmanager
def contract_fixture():
    """Synthetic JSON, archives and dependency inventories; no actual benchmark data."""
    with tempfile.TemporaryDirectory(prefix='cb-pool-fake-') as tmp:
        root=Path(tmp).resolve();data=root/'data';data.mkdir()
        tiny=data/'fake.parquet';tiny.write_bytes(b'OWNED_FAKE_NOT_PARQUET_NEVER_PARSED')
        dataset=reference(data/'manifest.json',{'files':[{'name':tiny.name,'sha256':sha(tiny)}]})
        inventory=[];ancestry=[];specs=[];rows={}
        for i,(instance_id,(repo,f2p_count,ptp_count)) in enumerate(r.TARGETS.items()):
            revision=hex(i+1)[2:]*40
            target={'instance_id':instance_id,'base_commit':revision}
            inventory.append({'target':target})
            ancestry.append({'target':target,'source_merge_is_ancestor':True,'status':'ANCESTRY_CONFIRMED'})
            path=root/(instance_id+'.tar.gz');archive(path,repo,revision)
            specs.append({'instance_id':instance_id,'repo':repo,'base_commit':revision,
                          'dataset_file':tiny.name,'archive':{'path':str(path),'sha256':sha(path)}})
            def labels(suite,count):
                return [('tests/fake/tests.py::FakeTests::test_' if repo=='django/django'
                         else 'sympy/core/tests/test_fake.py::test_')+suite+'_'+str(n) for n in range(count)]
            rows[instance_id]={'FAIL_TO_PASS':json.dumps(labels('f2p',f2p_count)),
                               'PASS_TO_PASS':json.dumps(labels('ptp',ptp_count)),
                               'problem_statement':'OWNED_FAKE_PUBLIC_TASK','test_patch':'FAKE_TEST_PATCH',
                               'patch':'FAKE_PRIVATE_REFERENCE_PATCH'}
        inventory_ref=reference(root/'inventory.json',{'qualification_candidates':inventory})
        ancestry_ref=reference(root/'ancestry.json',{'input':inventory_ref,'rows':ancestry})
        legacy=root/'legacy';binary=legacy/'bin/python';binary.parent.mkdir(parents=True)
        binary.write_bytes(b'OWNED_FAKE_BINARY_NEVER_EXECUTED')
        dependency_refs={}
        for kind,env_name in [('django','swe_contextbench_django_env_20261104'),
                              ('sympy','swe_contextbench_sympy_python38_env_20261104')]:
            env=root/env_name;site=env/'site/dep.py';wheel=env/'wheelhouse/dep.whl'
            site.parent.mkdir(parents=True);wheel.parent.mkdir();site.write_bytes(b'FAKE_SITE');wheel.write_bytes(b'FAKE_WHEEL')
            manifest={'site_files':{'dep.py':sha(site)},'wheels':{'dep.whl':sha(wheel)}}
            if kind=='sympy':manifest.update(container_image=r.IMAGE,python_binary_sha256=sha(binary))
            dependency_refs[kind]=reference(root/(kind+'_deps.json'),manifest)
        c={'schema':'contextbench_pool_qualification_v1','dataset_manifest':dataset,'ancestry':ancestry_ref,
           'cases':specs,'runtime':{'image':r.IMAGE,
                 'django_dependency_manifest':dependency_refs['django'],'sympy_dependency_manifest':dependency_refs['sympy']}}
        path=root/'CONTRACT.json';contract_sha=write(path,c)
        shared=SimpleNamespace(DATA=data,dataset_row=mock.Mock(side_effect=lambda spec:copy.deepcopy(rows[spec['id']])),
            extract_safe=mock.Mock(side_effect=AssertionError('no extraction in check')),
            apply_patch=mock.Mock(side_effect=AssertionError('no patching in check')))
        django=SimpleNamespace(regression_labels=mock.Mock(side_effect=lambda spec:
            (r.mapped_labels('django/django',json.loads(rows[spec['id']]['PASS_TO_PASS'])),[])),
            extract=mock.Mock(side_effect=AssertionError('no extraction in check')))
        with mock.patch.object(r,'ROOT',root),mock.patch.object(r,'LEGACY',legacy), \
                mock.patch.object(r,'helpers',return_value=(shared,django)):
            yield SimpleNamespace(root=root,data=data,c=c,path=path,sha=contract_sha,output=root/'FRESH_OUTPUT',
                                  shared=shared,django=django,rows=rows)


class FrozenContractTests(unittest.TestCase):
    def test_valid_static_contract_keeps_exact_published_counts_without_extraction(self):
        with contract_fixture() as f,mock.patch.object(r.subprocess,'run',side_effect=AssertionError('no Docker/process')):
            c=r.load_contract(f.path,f.sha,f.output)
            self.assertEqual([(len(row['labels']['f2p']),len(row['labels']['ptp'])) for row in c['cases']],
                             [(12,25),(2,320),(4,48)])
            self.assertEqual([row['spec']['instance_id'] for row in c['cases']],
                             ['django__django-31051','sympy__sympy-9384','sympy__sympy-19006'])
            f.shared.extract_safe.assert_not_called();f.shared.apply_patch.assert_not_called();f.django.extract.assert_not_called()
            self.assertFalse(f.output.exists())
            for limits in c['limits'].values():
                self.assertIn('Python3.8',limits)
                self.assertIn('full conda runtime library tree not frozen',limits)

    def test_duplicate_unknown_case_schema_hash_and_path_escape_are_rejected(self):
        for mode in ('duplicate','schema','hash','dataset_escape','unlisted_dataset','archive_escape','output_escape','existing_output',
                     'runtime_image','runtime_extra','unproven_ancestry'):
            with self.subTest(mode=mode),contract_fixture() as f:
                contract=copy.deepcopy(f.c);output=f.output
                if mode=='duplicate':contract['cases'][1]=contract['cases'][0]
                elif mode=='schema':contract['schema']='UNREVIEWED_QUALIFIER'
                elif mode=='dataset_escape':contract['cases'][0]['dataset_file']='../fake.parquet'
                elif mode=='unlisted_dataset':contract['cases'][0]['dataset_file']='not_in_manifest.parquet'
                elif mode=='archive_escape':contract['cases'][0]['archive']['path']=str(f.root/'../outside.tar.gz')
                elif mode=='output_escape':output=f.root/'../outside_output'
                elif mode=='existing_output':output.mkdir()
                elif mode=='runtime_image':contract['runtime']['image']='UNKNOWN_UNFROZEN_IMAGE'
                elif mode=='runtime_extra':contract['runtime']['host_network']=True
                elif mode=='unproven_ancestry':
                    ancestry=json.loads(Path(contract['ancestry']['path']).read_text())
                    ancestry['rows'][0]['source_merge_is_ancestor']=False
                    contract['ancestry']=reference(Path(contract['ancestry']['path']),ancestry)
                digest=write(f.path,contract)
                if mode=='hash':digest='f'*64
                with self.assertRaises((ValueError,FileExistsError)):
                    r.load_contract(f.path,digest,output)

    def test_unmapped_or_changed_published_counts_fail_before_any_container(self):
        for mode in ('unmapped','missing','duplicate'):
            with self.subTest(mode=mode),contract_fixture() as f, \
                    mock.patch.object(r.subprocess,'run',side_effect=AssertionError('no Docker')):
                key=list(r.TARGETS)[0];labels=json.loads(f.rows[key]['FAIL_TO_PASS'])
                if mode=='unmapped':labels[0]='unmapped_test_name'
                elif mode=='missing':labels.pop()
                else:labels[-1]=labels[0]
                f.rows[key]['FAIL_TO_PASS']=json.dumps(labels)
                with self.assertRaises(ValueError):r.load_contract(f.path,f.sha,f.output)

    def test_check_mode_writes_only_optional_exclusive_report_outside_output(self):
        with contract_fixture() as f:
            report=f.root/'CHECK.json'
            argv=['--check','--contract',str(f.path),'--contract-sha',f.sha,'--output',str(f.output),
                  '--check-report',str(report)]
            with mock.patch.object(r.subprocess,'run',side_effect=AssertionError('no Docker/process')), \
                    mock.patch.object(r,'execute',side_effect=AssertionError('no execution')), \
                    mock.patch('sys.stdout',new_callable=io.StringIO) as stdout:
                self.assertEqual(r.main(argv),0)
            self.assertEqual(json.loads(stdout.getvalue()),{'status':'CPU_CHECK_ONLY','cases':3,'model_calls':0})
            body=json.loads(report.read_text());self.assertEqual(body['container_runs'],0)
            self.assertFalse(f.output.exists())
            f.shared.extract_safe.assert_not_called();f.django.extract.assert_not_called()
            with self.assertRaises(FileExistsError):r.main(argv)
            inside=list(argv);inside[-1]=str(f.output/'CHECK.json')
            with self.assertRaises(ValueError):r.main(inside)


@contextmanager
def source_contract_fixture():
    with contract_fixture() as f:
        experience=f.data/'SWEContextBench_Lite_Experience.parquet';experience.write_bytes(b'OWNED_FAKE_EXPERIENCE')
        dataset=reference(f.data/'manifest.json',{'files':[{'name':experience.name,'sha256':sha(experience)}]})
        f.rows.clear();specs=[];pairs=[];registered=[]
        for i,(id,repo,ptp,target) in enumerate([('django__django-12453','django/django',5,'django__django-31051'),('sympy__sympy-21055','sympy/sympy',13,'sympy__sympy-9384')]):
            source={'instance_id':id,'repo':repo,'base_commit':str(i+4)*40};dest={'instance_id':target,'repo':repo,'base_commit':str(i+6)*40}
            pairs.append({'source':source,'target':dest,'status':'ANCESTRY_CONFIRMED','source_merge_is_ancestor':True})
            registered.append(dict(dest,earlier_experience_candidate=source))
            module='tests/backends/base/test_creation.py' if repo=='django/django' else 'sympy/assumptions/tests/test_refine.py'
            maps={};row={'problem_statement':'OWNED_FAKE_SOURCE','test_patch':'+++ b/'+module+'\n','patch':'OWNED_FAKE_GOLD'}
            for suite,count,field in [('f2p',1,'FAIL_TO_PASS'),('ptp',ptp,'PASS_TO_PASS')]:
                entries=[]
                for n in range(count):
                    method='test_'+suite+'_'+str(n);pub=method+' (backends.base.test_creation.FakeTests)' if repo=='django/django' else method
                    entries.append({'published':pub,'node':module+('::FakeTests::' if repo=='django/django' else '::')+method})
                maps[suite]=entries;row[field]=json.dumps([entry['published'] for entry in entries])
            f.rows[id]=row;path=f.root/(id+'.tar.gz');archive(path,repo,source['base_commit'])
            specs.append(dict(source,dataset_file=experience.name,archive={'path':str(path),'sha256':sha(path)},role='source',related_target_id=target,label_map=maps))
        inv=reference(f.root/'inventory.json',{'qualification_candidates':pairs})
        ancestry=reference(f.root/'ancestry.json',{'input':inv,'rows':pairs})
        registry=reference(f.root/'QUALIFIED.json',{'schema':'qualified_code_development_pool_v1','cases':registered})
        c=dict(f.c,schema='contextbench_pool_qualification_source_v2',dataset_manifest=dataset,ancestry=ancestry,cases=specs,qualified_targets=registry)
        f.c=c;f.sha=write(f.path,c)
        with mock.patch.object(r,'QUALIFIED_TARGETS_SHA',registry['sha256'],create=True):yield f


class SourceContractTests(unittest.TestCase):
    def test_source_v2_keeps_method_and_exact_two_source_counts_without_execution(self):
        with source_contract_fixture() as f,mock.patch.object(r.subprocess,'run',side_effect=AssertionError('no container')):
            c=r.load_contract(f.path,f.sha,f.output)
            self.assertEqual([case['spec']['instance_id'] for case in c['cases']],['django__django-12453','sympy__sympy-21055'])
            self.assertEqual([(len(case['labels']['f2p']),len(case['labels']['ptp'])) for case in c['cases']],[(1,5),(1,13)])
            self.assertEqual(c['cases'][0]['labels']['f2p'],['backends.base.test_creation.FakeTests.test_f2p_0'])
            f.django.regression_labels.assert_not_called();f.django.extract.assert_not_called();f.shared.extract_safe.assert_not_called()

    def test_source_identity_registry_and_complete_unambiguous_maps_fail_closed(self):
        for mode in ('role','related','base','qualified_hash','dataset','missing','extra','class_only','wrong_method','wrong_published','alias','sympy_module','sympy_name','ancestry_source','patch_module'):
            with self.subTest(mode=mode),source_contract_fixture() as f:
                c=copy.deepcopy(f.c);d,s=c['cases'];entry=d['label_map']['f2p'][0]
                if mode=='role':d['role']='target'
                elif mode=='related':d['related_target_id']=s['related_target_id']
                elif mode=='base':d['base_commit']='f'*40
                elif mode=='qualified_hash':c['qualified_targets']['sha256']='0'*64
                elif mode=='dataset':d['dataset_file']='fake.parquet'
                elif mode=='missing':d['label_map']['ptp'].pop()
                elif mode=='extra':d['label_map']['ptp'].append(dict(entry))
                elif mode=='class_only':entry['node']='tests/backends/base/test_creation.py::FakeTests'
                elif mode=='wrong_method':entry['node']+='WRONG'
                elif mode=='wrong_published':entry['published']='test_WRONG (backends.base.test_creation.FakeTests)'
                elif mode=='alias':d['label_map']['ptp'][0]['node']=entry['node']
                elif mode=='sympy_module':s['label_map']['f2p'][0]['node']='sympy/other/tests/test_refine.py::test_f2p_0'
                elif mode=='sympy_name':s['label_map']['f2p'][0]['node']+='WRONG'
                elif mode=='ancestry_source':
                    ancestry=json.loads(Path(c['ancestry']['path']).read_text());ancestry['rows'][0]['source']['base_commit']='f'*40
                    c['ancestry']=reference(Path(c['ancestry']['path']),ancestry)
                else:f.rows[s['instance_id']]['test_patch']='+++ b/sympy/other.py\n'
                with self.assertRaises(ValueError):r.load_contract(f.path,write(f.path,c),f.output)

    def test_validated_two_source_case_count_can_close_qualified_with_fake_test_controls(self):
        with source_contract_fixture() as f:
            c=r.load_contract(f.path,f.sha,f.output)
            def extract(archive,destination,revision):destination.mkdir();(destination/'LICENSE').write_text('OWNED_FAKE');return 1
            f.shared.extract_safe.side_effect=extract;f.django.extract.side_effect=extract
            f.shared.apply_patch.side_effect=None;f.shared.apply_patch.return_value={'check_exit':0,'apply_exit':0,'diagnostic':''}
            def tests(work,repo,labels,runner,log):return run_record(labels,['failed' if work.name=='base_with_tests' and log.name.endswith('_f2p.log') else 'passed']*len(labels))
            with mock.patch.object(r,'mem_available',return_value=8*1024**3),mock.patch.object(r,'run_tests',side_effect=tests):result=r.execute(c)
            self.assertEqual(result['status'],'QUALIFIED');self.assertEqual(len(result['cases']),2)


def run_record(labels,states,exit=None,fatal=None):
    if exit is None:exit=1 if 'failed' in states else 0
    record={'exit':exit,'result':{'tests':dict(zip(labels,states)),'fatal':fatal or []}}
    record['coverage']=r.classify(labels,record)
    return record


class PerTestOutcomeTests(unittest.TestCase):
    def test_full_runner_records_real_unittest_pass_assertion_failure_and_import_error(self):
        # Execute the complete wrapper in a CPU child, with synthetic public tests
        # only. The process isolates its unittest hooks from this test process.
        fake_tests='''import sys,unittest
class SyntheticPublicTests(unittest.TestCase):
 def test_passed(self):self.assertTrue(True)
 def test_failed(self):self.assertEqual("OWNED_FAKE_EXPECTED","OWNED_FAKE_ACTUAL")
 def test_import_error(self):raise ImportError("OWNED_FAKE_MISSING_MODULE")
suite=unittest.defaultTestLoader.loadTestsFromTestCase(SyntheticPublicTests)
result=unittest.TextTestRunner(verbosity=0).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
'''
        with tempfile.TemporaryDirectory(prefix='cb-runner-cpu-') as tmp:
            root=Path(tmp);(root/'tests').mkdir();(root/'tests/runtests.py').write_text(fake_tests,encoding='utf8')
            python=r.LEGACY/'bin/python'
            if not python.is_file():self.skipTest('frozen historical Python3.8 is unavailable')
            done=subprocess.run([str(python),'-c',r.RUNNER,'django'],cwd=root,stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20,
                env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        self.assertEqual(done.returncode,1,done.stderr.decode('utf8',errors='replace'))
        markers=[line[len(r.MARKER):] for line in done.stdout.decode('utf8').splitlines() if line.startswith(r.MARKER)]
        self.assertEqual(len(markers),1)
        payload=json.loads(markers[0]);prefix='__main__.SyntheticPublicTests.'
        self.assertEqual(payload,{'tests':{prefix+'test_passed':'passed',prefix+'test_failed':'failed',
            prefix+'test_import_error':'error'},'fatal':[]})
        self.assertFalse(r.classify(list(payload['tests']),{'exit':done.returncode,'result':payload})['complete'])

    def test_pytest_wrapper_distinguishes_xfail_xpass_and_strict_xpass_on_python38(self):
        python=r.LEGACY/'bin/python'
        if not python.is_file():self.skipTest('frozen historical Python3.8 is unavailable')
        fake_tests='''import pytest
@pytest.mark.xfail(reason="OWNED_FAKE_expected_failure")
def test_expected_fail():assert False
@pytest.mark.xfail(reason="OWNED_FAKE_unexpected_pass",strict=False)
def test_unexpected_pass():assert True
@pytest.mark.xfail(reason="OWNED_FAKE_strict_pass",strict=True)
def test_strict_pass():assert True
@pytest.fixture
def setup_xfail():pytest.xfail("OWNED_FAKE_setup_xfail")
def test_setup_xfail(setup_xfail):assert True
'''
        with tempfile.TemporaryDirectory(prefix='cb-pytest-cpu-') as tmp:
            root=Path(tmp);(root/'test_public.py').write_text(fake_tests,encoding='utf8')
            labels=['test_public.py::'+name for name in ('test_expected_fail','test_unexpected_pass','test_strict_pass','test_setup_xfail')]
            done=subprocess.run([str(python),'-c',r.RUNNER,'sympy',*labels],cwd=root,stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20,env={**os.environ,
                'PYTHONPATH':str(r.ROOT/'swe_contextbench_sympy_python38_env_20261104/site'),
                'PYTHONDONTWRITEBYTECODE':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
        self.assertEqual(done.returncode,1,done.stderr.decode('utf8',errors='replace'))
        markers=[s[len(r.MARKER):] for s in done.stdout.decode('utf8').splitlines() if s.startswith(r.MARKER)]
        self.assertEqual(len(markers),1)
        payload=json.loads(markers[0]);self.assertEqual(payload['fatal'],[])
        self.assertEqual(payload['tests'],dict(zip(labels,('xfailed','xpassed','failed','xfailed'))))
        record={'exit':done.returncode,'result':payload};record['coverage']=r.classify(labels,record)
        self.assertFalse(record['coverage']['complete'])
        self.assertFalse(r.qualification(record,record,record,record)['qualified'])

    def test_mixed_base_results_are_not_all_fail_to_pass_reproduction(self):
        labels=['sympy/test_fake.py::test_a','sympy/test_fake.py::test_b']
        mixed=run_record(labels,['failed','passed'])
        passing=run_record(labels,['passed','passed'])
        result=r.qualification(mixed,passing,passing,passing)
        self.assertFalse(result['qualified']);self.assertFalse(result['base_all_f2p_reproduced'])
        self.assertTrue(result['gold_all_f2p_pass']);self.assertTrue(result['base_all_ptp_pass'])

    def test_every_published_f2p_fails_and_both_ptp_controls_pass(self):
        labels=['sympy/test_fake.py::test_a','sympy/test_fake.py::test_b']
        failing=run_record(labels,['failed','failed']);passing=run_record(labels,['passed','passed'])
        self.assertTrue(r.qualification(failing,passing,passing,passing)['qualified'])
        self.assertEqual(failing['coverage']['labels'],dict.fromkeys(labels,'failed'))

    def test_import_collection_skip_missing_extra_or_bad_exit_is_not_reproduction(self):
        labels=['sympy/test_fake.py::test_a','sympy/test_fake.py::test_b']
        passing=run_record(labels,['passed','passed'])
        for mode in ('import','collection','skip','missing','extra','exit'):
            with self.subTest(mode=mode):
                record=run_record(labels,['failed','failed'])
                if mode=='import':record['result']['tests'][labels[0]]='error'
                elif mode=='collection':record['result']['fatal']=['collection_error']
                elif mode=='skip':record['result']['tests'][labels[0]]='skipped'
                elif mode=='missing':record['result']['tests'].pop(labels[0])
                elif mode=='extra':record['result']['tests']['UNREQUESTED_TEST']='failed'
                else:record['exit']=2
                record['coverage']=r.classify(labels,record)
                self.assertFalse(record['coverage']['complete'])
                self.assertFalse(r.qualification(record,passing,passing,passing)['qualified'])


class ContainerBoundaryTests(unittest.TestCase):
    def test_command_has_fixed_low_resource_network_and_readonly_limits(self):
        for repo in ('django/django','sympy/sympy'):
            with self.subTest(repo=repo):
                argv=r.command(Path('/OWNED_FAKE/work'),repo,['FAKE_TEST'],Path('/OWNED_FAKE/runner.py'),'OWNED_FAKE_NAME')
                for flag,value in (('--network','none'),('--cpus','1'),('--memory','1g'),('--pids-limit','256'),
                                   ('--cap-drop','ALL'),('--security-opt','no-new-privileges'),('--pull','never')):
                    self.assertEqual(argv[argv.index(flag)+1],value)
                self.assertIn('--read-only',argv);self.assertIn('--rm',argv)
                mounts=[argv[i+1] for i,x in enumerate(argv) if x=='--mount']
                self.assertTrue(all(x.endswith(',readonly') for x in mounts))
                self.assertFalse(any('docker.sock' in x for x in argv))
                self.assertEqual(argv[argv.index('--name')+1],'OWNED_FAKE_NAME')
                self.assertEqual(argv[argv.index('--entrypoint')+1],'/opt/legacy/bin/python')
                self.assertIn('type=bind,src='+str(r.LEGACY)+',dst=/opt/legacy,readonly',mounts)
                site='django_env_20261104' if repo=='django/django' else 'sympy_python38_env_20261104'
                self.assertIn('type=bind,src='+str(r.ROOT/('swe_contextbench_'+site)/'site')+',dst=/deps,readonly',mounts)

    def test_timeout_removes_only_its_generated_owned_container_and_keeps_partial_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log=Path(tmp)/'tests.log';calls=[]
            def process(argv,**kwargs):
                calls.append(argv)
                if argv[:2]==['docker','run']:
                    raise subprocess.TimeoutExpired(argv,240,output=b'OWNED_FAKE_PARTIAL_OUTPUT\n')
                self.assertEqual(argv,['docker','rm','-f','cb-pool-123-456'])
                return subprocess.CompletedProcess(argv,0)
            with mock.patch.object(r,'mem_available',return_value=8*1024**3), \
                    mock.patch.object(r.os,'getpid',return_value=123), \
                    mock.patch.object(r.time,'monotonic_ns',return_value=456), \
                    mock.patch.object(r.subprocess,'run',side_effect=process):
                result=r.run_tests(Path('/OWNED_FAKE/work'),'sympy/sympy',['sympy/test_fake.py::test_a'],Path('/OWNED_FAKE/runner.py'),log)
            self.assertEqual(result['exit'],124);self.assertFalse(result['coverage']['complete'])
            self.assertEqual(log.read_bytes(),b'OWNED_FAKE_PARTIAL_OUTPUT\n')
            self.assertEqual(result['log_sha256'],sha(log));self.assertEqual(len(calls),2)
            self.assertEqual(json.loads(log.with_suffix('.command.json').read_text())['container'],'cb-pool-123-456')

    def test_failed_or_timed_out_owned_cleanup_preserves_partial_output_and_failure_evidence(self):
        for mode in ('nonzero','timeout'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                log=Path(tmp)/'tests.log';partial=b'OWNED_FAKE_PARTIAL_BEFORE_CLEANUP\n';calls=[]
                cleanup_output=b'OWNED_FAKE_CLEANUP_DIAGNOSTIC\n'
                def process(argv,**kwargs):
                    calls.append(argv)
                    if argv[:2]==['docker','run']:
                        raise subprocess.TimeoutExpired(argv,240,output=partial)
                    self.assertEqual(argv,['docker','rm','-f','cb-pool-123-456'])
                    # The original test output must already exist even when the
                    # cleanup command itself fails or never returns normally.
                    self.assertEqual(log.read_bytes(),partial)
                    if mode=='timeout':raise subprocess.TimeoutExpired(argv,15,output=cleanup_output)
                    return subprocess.CompletedProcess(argv,1,stdout=cleanup_output)
                with mock.patch.object(r,'mem_available',return_value=8*1024**3), \
                        mock.patch.object(r.os,'getpid',return_value=123), \
                        mock.patch.object(r.time,'monotonic_ns',return_value=456), \
                        mock.patch.object(r.subprocess,'run',side_effect=process):
                    result=r.run_tests(Path('/OWNED_FAKE/work'),'sympy/sympy',['sympy/test_fake.py::test_a'],
                                       Path('/OWNED_FAKE/runner.py'),log)
                self.assertEqual(result['status'],'CLEANUP_FAILED')
                self.assertEqual(result['exit'],124);self.assertFalse(result['coverage']['complete'])
                self.assertEqual(log.read_bytes(),partial);self.assertEqual(result['log_sha256'],sha(log))
                self.assertEqual(calls[1],['docker','rm','-f','cb-pool-123-456']);self.assertEqual(len(calls),2)
                cleanup=result['cleanup'];self.assertEqual(cleanup['argv'],calls[1])
                self.assertEqual(cleanup['exit'],None if mode=='timeout' else 1)
                if mode=='timeout':self.assertEqual(cleanup['error'],'TimeoutExpired')
                self.assertEqual(log.with_suffix('.cleanup.log').read_bytes(),cleanup_output)
                self.assertEqual(cleanup['log_sha256'],sha(log.with_suffix('.cleanup.log')))

    def test_memavailable_gate_defers_without_container_or_extraction(self):
        with contract_fixture() as f,mock.patch.object(r,'mem_available',return_value=4*1024**3-1), \
                mock.patch.object(r.subprocess,'run',side_effect=AssertionError('no Docker at low memory')):
            record=r.run_tests(Path('/OWNED_FAKE/work'),'sympy/sympy',['FAKE_TEST'],Path('/OWNED_FAKE/runner.py'),f.root/'tests.log')
            self.assertEqual(record['status'],'DEFERRED');self.assertFalse((f.root/'tests.log').exists())
            c=r.load_contract(f.path,f.sha,f.output);result=r.execute(c)
            self.assertEqual(result['status'],'DEFERRED')
            self.assertEqual(result['model_calls'],0);self.assertEqual(result['cases'],{})
            f.shared.extract_safe.assert_not_called();f.shared.apply_patch.assert_not_called();f.django.extract.assert_not_called()


if __name__=='__main__':
    unittest.main()
