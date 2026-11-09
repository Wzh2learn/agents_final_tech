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



@contextmanager
def matplotlib_contract_fixture():
    """Synthetic pair/projection; no benchmark gold, Docker or actor use."""
    with contract_fixture() as f:
        specs=[];rows={}
        for case,(revision,role,dataset,f2p,ptp,module) in r.MPL_CASES.items():
            path=f.root/(case+'.tar.gz');archive(path,'matplotlib/matplotlib',revision)
            labels={'f2p':[module+'::test_f2p'], 'ptp':[module+'::test_ptp_'+str(i) for i in range(ptp)]}
            rows[case]=dict(problem_statement='CPU_PUBLIC_'+case,test_patch='+++ b/'+module+'\n',patch='CPU_EVAL_ONLY_REFERENCE',
                FAIL_TO_PASS=json.dumps(labels['f2p']),PASS_TO_PASS=json.dumps(labels['ptp']))
            (f.data/dataset).write_bytes(b'CPU_SYNTHETIC_DATASET_NOT_PARSED')
            specs.append(dict(instance_id=case,repo='matplotlib/matplotlib',base_commit=revision,role=role,
                dataset_file=dataset,archive={'path':str(path),'sha256':sha(path)},dependency_slot='source',
                problem_sha256=hashlib.sha256(rows[case]['problem_statement'].encode()).hexdigest(),
                label_map={k:[dict(published=x,node=x) for x in v] for k,v in labels.items()}))
        pair={kind:{k:spec[k] for k in ('instance_id','repo','base_commit')} for kind,spec in zip(('source','target'),specs)}
        selection=reference(f.root/'mpl_selection.json',{'pairs':[pair]})
        ancestry=reference(f.root/'mpl_ancestry.json',{'schema':'code_source_second_wave_ancestry_v1','selection_sha256':selection['sha256'],
            'results':[dict(repo='matplotlib/matplotlib',source=specs[0]['instance_id'],target=specs[1]['instance_id'],target_base=specs[1]['base_commit'],status='ANCESTRY_PASS_METADATA_ONLY')]})
        runtime={'image':r.IMAGE,'projection':{'path':str(f.root/'projection/manifest.json'),'sha256':'a'*64},
            'native_overlays':{'source':{'path':str(f.root/'native.json'),'sha256':'b'*64},'target':{'path':str(f.root/'native2.json'),'sha256':'c'*64}}}
        dataset_ref=reference(f.data/'mpl_manifest.json',{'files':[{'name':n,'sha256':sha(f.data/n)} for n in {v[2] for v in r.MPL_CASES.values()}]})
        c=dict(schema='contextbench_pool_qualification_matplotlib_pair_v1',dataset_manifest=dataset_ref,selection=selection,ancestry=ancestry,cases=specs,runtime=runtime)
        f.shared.dataset_row.side_effect=lambda spec:copy.deepcopy(rows[spec['id']])
        helper=SimpleNamespace(extract=mock.Mock(),overlay=mock.Mock(return_value={}))
        assets=dict(runtime=str(f.root/'projection/runtime'),sites={k:str(f.root/'projection/deps'/k) for k in ('source','target')},native_sites={'source':'CPU_NATIVE_SOURCE','target':'CPU_NATIVE_TARGET'},overlays={'source':{},'target':{}},helper=helper)
        with mock.patch.object(r,'matplotlib_assets',return_value=assets):
            f.c=c;f.sha=write(f.path,c);f.assets=assets;f.mpl_rows=rows;yield f


class MatplotlibPairTests(unittest.TestCase):
    def test_exact_matplotlib_nodes_are_supported_without_rewriting_published_labels(self):
        labels=['lib/matplotlib/tests/test_pickle.py::test_complete[png]']
        self.assertEqual(r.mapped_labels('matplotlib/matplotlib',labels),labels)

    def test_new_pair_check_binds_raw_problem_counts_and_never_extracts_or_runs(self):
        with matplotlib_contract_fixture() as f,mock.patch.object(subprocess,'run',side_effect=AssertionError('CPU check cannot run')):
            result=r.load_contract(f.path,f.sha,f.output)
            self.assertEqual([(len(x['labels']['f2p']),len(x['labels']['ptp'])) for x in result['cases']],[(1,181),(1,60)])
            self.assertEqual(result['mode'],'matplotlib_pair');self.assertFalse(f.output.exists())
            self.assertFalse(f.assets['helper'].extract.called);self.assertFalse(f.assets['helper'].overlay.called)

    def test_pair_schema_mapping_raw_hash_and_ancestry_changes_fail_closed(self):
        with matplotlib_contract_fixture() as f:
            for edit in ('duplicate','base','role','raw_problem','node_alias','missing_label','slot','ancestry'):
                c=copy.deepcopy(f.c)
                if edit=='duplicate':c['cases'][1]=copy.deepcopy(c['cases'][0])
                elif edit=='base':c['cases'][0]['base_commit']='0'*40
                elif edit=='role':c['cases'][0]['role']='target'
                elif edit=='raw_problem':c['cases'][0]['problem_sha256']='0'*64
                elif edit=='node_alias':c['cases'][0]['label_map']['f2p'][0]['node']=c['cases'][0]['label_map']['ptp'][0]['node']
                elif edit=='missing_label':c['cases'][0]['label_map']['ptp'].pop()
                elif edit=='slot':c['cases'][0]['dependency_slot']='unapproved'
                else:c['ancestry']=reference(f.root/'wrong_ancestry.json',{'schema':'code_source_second_wave_ancestry_v1','selection_sha256':c['selection']['sha256'],'results':[]})
                with self.subTest(edit=edit),self.assertRaises(ValueError):r.load_contract(f.path,write(f.path,c),f.output)

    def test_ast_node_mapping_keeps_params_complete_nodes_and_top_level_functions(self):
        module='lib/matplotlib/tests/test_cbook.py'
        source='class TestBox:\n def test_bad_dims(self): pass\nclass TestCallback:\n def test_callback(self): pass\ndef test_grouper_private(): pass\n'
        labels=[module+'::test_bad_dims',module+'::test_callback[False]',module+'::TestCallback::test_callback[True]',module+'::test_grouper_private']
        before=labels.copy();expected=[module+'::TestBox::test_bad_dims',module+'::TestCallback::test_callback[False]',labels[2],labels[3]]
        self.assertEqual(r.resolve_matplotlib_nodes(module,source,labels),expected);self.assertEqual(labels,before)

    def test_ast_node_mapping_rejects_missing_ambiguous_partial_and_duplicate_aliases(self):
        module='lib/matplotlib/tests/test_cbook.py';source='class A:\n def test_same(self): pass\nclass B:\n def test_same(self): pass\n'
        for labels in [[module+'::test_same'],[module+'::test_missing'],[module+'::UNKNOWN::test_same']]:
            with self.subTest(labels=labels),self.assertRaises(ValueError):r.resolve_matplotlib_nodes(module,source,labels)
        source='class A:\n def test_same(self): pass\n'
        with self.assertRaises(ValueError):r.resolve_matplotlib_nodes(module,source,[module+'::test_same',module+'::A::test_same'])

    def test_ast_contract_binds_public_file_and_rejects_missing_function_or_forged_mapping(self):
        with matplotlib_contract_fixture() as f:
            f.c['schema']='contextbench_pool_qualification_matplotlib_pair_v2'
            f.c['mapping_origin']=dict(policy='exact_or_unique_ast_class_path_v1',prior_runs=[reference(f.root/'run1.json',dict(status='ERROR',container_runs=1,seconds=.1)),reference(f.root/'run2.json',dict(status='ERROR',container_runs=3,seconds=.1))],prior_code_snapshot=reference(f.root/'snapshot.json',{'files':[]}),caps=dict(container_runs=4,group_seconds=300,seconds=900),target_task_nature='maintenance_followup_not_independent_bug')
            for spec in f.c['cases']:
                code='def test_f2p(): pass\n'
                target=spec['role']=='target'
                code+=('class TestPublic:\n' if target else '')+'\n'.join((' ' if target else '')+'def '+e['published'].split('::')[-1]+'('+('self' if target else '')+'): pass' for e in spec['label_map']['ptp'])+'\n'
                path=f.root/(spec['role']+'_public_tests.py');path.write_text(code);spec['node_source']={'path':str(path),'sha256':sha(path)}
                if target:
                    for e in spec['label_map']['ptp']:e['node']=e['node'].replace('::','::TestPublic::',1)
            result=r.load_contract(f.path,write(f.path,f.c),f.output);self.assertEqual(result['caps']['seconds'],900)
            self.assertEqual(result['mapping_counts'],{'matplotlib__matplotlib-25332':0,'matplotlib__matplotlib-25352':60})
            third=reference(f.root/'run3.json',dict(status='ERROR',container_runs=3,seconds=.2))
            f.c['mapping_origin']['prior_runs'].append(third)
            result=r.load_contract(f.path,write(f.path,f.c),f.output)
            self.assertEqual(sum(x['container_runs'] for x in result['prior_controls']),7)
            for duplicate in ('same_path','same_bytes_other_path'):
                invalid=copy.deepcopy(f.c)
                invalid['mapping_origin']['prior_runs'][2]=(invalid['mapping_origin']['prior_runs'][1] if duplicate=='same_path' else reference(f.root/'copied_run2.json',dict(status='ERROR',container_runs=3,seconds=.1)))
                with self.subTest(duplicate=duplicate),self.assertRaises(ValueError):r.load_contract(f.path,write(f.path,invalid),f.output)

            c=copy.deepcopy(f.c);c['cases'][1]['label_map']['ptp'][0]['node']=c['cases'][1]['label_map']['ptp'][0]['published']
            with self.assertRaises(ValueError):r.load_contract(f.path,write(f.path,c),f.output)
            path=Path(f.c['cases'][1]['node_source']['path']);path.write_text('def only_unrelated(): pass\n')
            f.c['cases'][1]['node_source']['sha256']=sha(path)
            with self.assertRaises(ValueError):r.load_contract(f.path,write(f.path,f.c),f.output)

    def test_warning_compatibility_is_exact_and_product_warning_remains_an_error(self):
        options=r.matplotlib_warning_options(r.MPL_WARNING_RULES)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);test=root/'test_warning_control.py'
            test.write_text("import warnings\ndef test_known():\n    exec(\"import warnings; warnings.warn('pkg_resources is deprecated as an API', DeprecationWarning)\", {'__name__':'pkg_resources'})\ndef test_product():\n    exec(\"import warnings; warnings.warn('pkg_resources is deprecated as an API', DeprecationWarning)\", {'__name__':'matplotlib._api'})\n")
            done=subprocess.run([sys.executable,'-m','pytest','-q','-W','error',*options,str(test)],cwd=root,capture_output=True,timeout=30,env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'))
            self.assertEqual(done.returncode,1,done.stdout.decode());self.assertIn('1 failed, 1 passed',done.stdout.decode())
        changed=copy.deepcopy(r.MPL_WARNING_RULES);changed[0]['module']='.*'
        with self.assertRaises(ValueError):r.matplotlib_warning_options(changed)

    def test_group_preserves_actual_exit_and_never_turns_skip_missing_or_signal_into_pass(self):
        labels={'f2p':['f'],'ptp':['p']}
        base={'exit':1,'result':{'tests':{'f':'failed','p':'passed'},'fatal':[]}}
        gold={'exit':0,'result':{'tests':{'f':'passed','p':'passed'},'fatal':[]}}
        self.assertTrue(r.matplotlib_qualification(base,gold,labels)['qualified']);self.assertEqual(base['exit'],1)
        for value in ('failed','skipped','xfailed','xpassed','missing'):
            bad=copy.deepcopy(base)
            if value=='missing':bad['result']['tests'].pop('p')
            else:bad['result']['tests']['p']=value
            with self.subTest(value=value):self.assertFalse(r.matplotlib_qualification(bad,gold,labels)['qualified'])
        for code in (137,-9,2):
            bad=copy.deepcopy(base);bad['exit']=code;self.assertFalse(r.matplotlib_qualification(bad,gold,labels)['qualified'])

    def test_matplotlib_command_has_python310_exact_nodes_offline_readonly_and_owned_cid(self):
        assets={'runtime':'/CPU/runtime','sites':{'source':'/CPU/deps/source'}}
        cmd=r.matplotlib_command(Path('/CPU/work'),['lib/matplotlib/tests/test_pickle.py::test_complete[png]'],Path('/CPU/runner.py'),'CPU_NAME',Path('/CPU/cid'),assets,'source')
        self.assertEqual(cmd[cmd.index('--network')+1],'none');self.assertIn('--read-only',cmd)
        self.assertEqual(cmd[cmd.index('--cpus')+1],'1');self.assertEqual(cmd[cmd.index('--memory')+1],'4g')
        self.assertEqual(cmd[cmd.index('--cidfile')+1],'/CPU/cid');self.assertIn('PYTHONPATH=/workspace/lib:/deps',cmd)
        self.assertEqual(cmd[cmd.index('--entrypoint')+1],'/extra/bin/python');self.assertIn('matplotlib',cmd)
        self.assertTrue(all('readonly' in cmd[i+1] for i,x in enumerate(cmd[:-1]) if x=='--mount'))

    def test_missing_or_mismatched_owned_cid_never_removes_an_unknown_container(self):
        with tempfile.TemporaryDirectory() as tmp:
            cid=Path(tmp)/'cid';cid.write_text('a'*64);calls=[]
            def inspect(cmd,**kw):calls.append(cmd);return SimpleNamespace(returncode=0,stdout=b'"/OTHER_OWNER"',stderr=b'')
            with mock.patch.object(subprocess,'run',side_effect=inspect),self.assertRaises(ValueError):r.matplotlib_cleanup(cid,'CPU_OWNED')
            self.assertEqual(len(calls),1);self.assertEqual(calls[0][:2],['docker','inspect'])

    def test_execute_uses_only_four_combined_groups_and_never_applies_gold_to_clean_base(self):
        with matplotlib_contract_fixture() as f:
            loaded=r.load_contract(f.path,f.sha,f.output);f.shared.apply_patch.side_effect=lambda *a:{'check_exit':0,'apply_exit':0}
            def extract(archive,base,rev):base.mkdir();(base/'clean.py').write_bytes(b'CPU_PUBLIC_BASE');return {}
            f.assets['helper'].extract.side_effect=extract
            groups=[]
            def group(work,labels,runner,log,assets,slot,timeout):
                groups.append((work.name,len(labels),timeout));states={n:'failed' if work.name=='base_with_tests' and 'test_f2p' in n else 'passed' for n in labels}
                return dict(exit=1 if 'failed' in states.values() else 0,result=dict(tests=states,fatal=[]),cleanup=dict(status='ALREADY_REMOVED'),container_started=True,seconds=.01)
            with mock.patch.object(r,'mem_available',return_value=8*1024**3),mock.patch.object(r,'run_matplotlib_group',side_effect=group):result=r.execute(loaded)
            self.assertEqual(result['status'],'QUALIFIED');self.assertEqual(len(groups),4)
            for case in result['cases'].values():self.assertTrue(case['qualification']['qualified'])
            self.assertEqual(sum('CPU_EVAL_ONLY_REFERENCE'==x.args[1] for x in f.shared.apply_patch.call_args_list),2)

@contextmanager
def matplotlib_source_contract_fixture(instance_id='matplotlib__matplotlib-90001'):
    """A fake source row, archive and test outcomes; no benchmark or container."""
    with contract_fixture() as f:
        revision='a'*40
        data_name='SWEContextBench_Lite_Experience.parquet'
        (f.data/data_name).write_bytes(b'FAKE_PARQUET_NO_REAL_READER')
        dataset=reference(f.data/'source_manifest.json',{'files':[{'name':data_name,'sha256':sha(f.data/data_name),'bytes':(f.data/data_name).stat().st_size}]})
        source_archive=f.root/'source.tar.gz';archive(source_archive,'matplotlib/matplotlib',revision)
        labels={'f2p':['lib/matplotlib/tests/test_fake.py::test_fix'],
                'ptp':['lib/matplotlib/tests/test_fake.py::test_old',
                       'lib/matplotlib/tests/test_other.py::test_old_too']}
        row=dict(instance_id=instance_id,base_commit=revision,problem_statement='CPU_PUBLIC_TASK',
                 test_patch='+++ b/lib/matplotlib/tests/test_fake.py\nCPU_TEST_ONLY',
                 patch='CPU_EVALUATOR_GOLD',FAIL_TO_PASS=json.dumps(labels['f2p']),
                 PASS_TO_PASS=json.dumps(labels['ptp']))
        meta=dict(instance_id=instance_id,base_commit=revision,repo='matplotlib/matplotlib')
        f.shared.dataset_row.side_effect=lambda spec:copy.deepcopy(row)
        f.shared.pq=SimpleNamespace(read_table=mock.Mock(side_effect=lambda *a,**kw:
            SimpleNamespace(to_pylist=lambda:[copy.deepcopy(meta)])))
        helper=SimpleNamespace(extract=mock.Mock(),overlay=mock.Mock(return_value={}))
        assets=dict(runtime=str(f.root/'projection/runtime'),sites={'source':str(f.root/'projection/deps/source')},
                    native_sites={'source':'CPU_NATIVE_SOURCE'},overlays={'source':{}},helper=helper)
        runtime={'image':r.IMAGE,'projection':{'path':str(f.root/'projection/manifest.json'),'sha256':'a'*64},
                 'native_overlays':{'source':{'path':str(f.root/'native.json'),'sha256':'b'*64},
                                    'target':{'path':str(f.root/'native2.json'),'sha256':'c'*64}}}
        spec=dict(instance_id=instance_id,repo='matplotlib/matplotlib',base_commit=revision,
                  dataset_file=data_name,role='DEVELOPMENT_SOURCE',
                  archive={'path':str(source_archive),'sha256':sha(source_archive)},dependency_slot='source',
                  problem_sha256=hashlib.sha256(row['problem_statement'].encode()).hexdigest(),
                  label_map={k:[dict(published=x,node=x) for x in v] for k,v in labels.items()})
        c=dict(schema='contextbench_pool_qualification_matplotlib_source_v1',
               dataset_manifest=dataset,cases=[spec],runtime=runtime)
        with mock.patch.object(r,'matplotlib_assets',return_value=assets):
            f.c=c;f.sha=write(f.path,c);f.assets=assets;f.source_row=row;f.source_meta=meta;yield f


@contextmanager
def matplotlib_source_collection_fixture():
    with matplotlib_source_contract_fixture() as f:
        module='lib/matplotlib/tests/test_fake.py'
        truncated=module+'::test_grid[rect0-Incorrect'
        complete=truncated+' size]'
        f.source_row['PASS_TO_PASS']=json.dumps([truncated])
        f.c['cases'][0]['label_map']['ptp']=[dict(published=truncated,node=truncated)]
        original=copy.deepcopy(f.c);original_path=f.root/'original_source_contract.json'
        original_ref=reference(original_path,original)
        previous=f.root/'previous';previous.mkdir();case_id=original['cases'][0]['instance_id']
        base=previous/case_id/'base_with_tests';path=base/module;path.parent.mkdir(parents=True)
        path.write_text('FAKE_TEST_MODULE_WITHOUT_REAL_TESTS')
        old_case=dict(spec=copy.deepcopy(original['cases'][0]),
            input_sha256={'test.patch':hashlib.sha256(f.source_row['test_patch'].encode()).hexdigest()},
            labels={'f2p':[x['node'] for x in original['cases'][0]['label_map']['f2p']],
                    'ptp':[truncated]},arms={'base_with_tests':{'tree_sha256':{module:sha(path)},
                    'group':dict(container_started=True,exit=4,cleanup={'status':'ALREADY_REMOVED'})}})
        origin=reference(previous/'receipt.json',dict(schema='matplotlib_source_qualification_result_v1',
            status='ERROR',model_calls=0,training=0,input_sha256={str(original_path):original_ref['sha256']},
            cases={case_id:old_case}))
        collection_log=f.root/'collection.log'
        nodeids=[original['cases'][0]['label_map']['f2p'][0]['node'],complete,module+'::unrelated']
        collection_log.write_text('CONTEXTBENCH_COLLECTION='+json.dumps({'nodeids':nodeids})+'\n')
        collection=dict(schema='matplotlib_source_node_collection_v1',status='COLLECTED',
            source_contract=original_ref,qualification_receipt=origin,instance_id=case_id,
            repo='matplotlib/matplotlib',base_commit=original['cases'][0]['base_commit'],modules={module:sha(path)},
            collection_log={'path':str(collection_log),'sha256':sha(collection_log)},
            execution=dict(container_started=True,exit=0,cleanup_status='ALREADY_REMOVED'))
        collection_path=f.root/'collection.json';f.c['node_collection']=reference(collection_path,collection)
        f.c['cases'][0]['label_map']['ptp'][0]['node']=complete
        f.collection=collection;f.collection_path=collection_path;f.collection_log=collection_log
        f.collection_module=path;f.collection_ids=nodeids;f.original=original;yield f


class MatplotlibSourceOnlyTests(unittest.TestCase):
    def test_expected_skip_keeps_full_denominator_and_never_exempts_failures(self):
        labels={'f2p':['f'], 'ptp':['p','lib/matplotlib/tests/test_widgets.py::test_rect_visibility[pdf]']}
        skip=labels['ptp'][1]
        base={'exit':1,'result':{'tests':{'f':'failed','p':'passed',skip:'skipped'},'fatal':[]}}
        gold={'exit':0,'result':{'tests':{'f':'passed','p':'passed',skip:'skipped'},'fatal':[]}}
        self.assertFalse(r.exact_coverage(labels['f2p']+labels['ptp'],base)['complete'])
        self.assertTrue(r.exact_coverage(labels['f2p']+labels['ptp'],base,expected_skips=[skip])['complete'])
        result=r.matplotlib_qualification(base,gold,labels,expected_skips=[skip])
        self.assertTrue(result['qualified']);self.assertFalse(result['base_all_ptp_pass']);self.assertFalse(result['gold_all_ptp_pass'])
        self.assertEqual(result['base_ptp_counts'],{'total':2,'passed':1,'skipped':1,'other':0})
        self.assertEqual(result['runtime_scope'],'LIMITED_RUNTIME_SCOPE')
        for mode in ('other_failed','missing_skip','extra_skip','f2p_pass','gold_f2p_fail'):
            b=copy.deepcopy(base);g=copy.deepcopy(gold)
            if mode=='other_failed':b['result']['tests']['p']='failed'
            elif mode=='missing_skip':g['result']['tests'][skip]='passed'
            elif mode=='extra_skip':g['result']['tests']['p']='skipped'
            elif mode=='f2p_pass':b['result']['tests']['f']='passed'
            else:g['result']['tests']['f']='failed'
            with self.subTest(mode=mode):self.assertFalse(r.matplotlib_qualification(b,g,labels,expected_skips=[skip])['qualified'])

    def test_expected_skip_passes_source_group_guard_without_changing_strict_coverage(self):
        with matplotlib_source_contract_fixture() as f:
            loaded=r.load_contract(f.path,f.sha,f.output);skip=loaded['cases'][0]['labels']['ptp'][1]
            policy={'nodes':[skip],'origin_receipt':{'path':'CPU_FAKE','sha256':'0'*64},'reason':'CPU_FAKE'}
            loaded['expected_skips']=[skip];loaded['contract']['expected_skips']=policy
            def extract(_archive,base,_revision):base.mkdir();(base/'public.py').write_text('CPU_PUBLIC');return {}
            f.assets['helper'].extract.side_effect=extract
            f.shared.apply_patch.side_effect=lambda *args:{'check_exit':0,'apply_exit':0}
            def group(work,labels,_runner,log,_assets,_slot,_timeout):
                base=work.name=='base_with_tests'
                states={n:('skipped' if n==skip else 'failed' if base and 'test_fix' in n else 'passed') for n in labels}
                result={'tests':states,'fatal':[]};log.write_text(r.MARKER+json.dumps(result)+'\n')
                record=dict(exit=1 if base else 0,result=result,log_sha256=sha(log),
                            cleanup={'status':'ALREADY_REMOVED'},container_started=True)
                record['coverage']=r.exact_coverage(labels,record);return record
            with mock.patch.object(r,'mem_available',return_value=8*1024**3),mock.patch.object(r,'run_matplotlib_group',side_effect=group):
                result=r.execute(loaded)
            case=result['cases'][f.c['cases'][0]['instance_id']]
            self.assertEqual(result['status'],'QUALIFIED');self.assertEqual(result['expected_skips'],policy)
            self.assertEqual(result['qualification_scope'],'LIMITED_RUNTIME_SCOPE')
            self.assertEqual(case['qualification']['base_ptp_counts'],{'total':2,'passed':1,'skipped':1,'other':0})
            for arm in ('base_with_tests','gold_with_tests'):
                self.assertFalse(case['arms'][arm]['group']['coverage']['complete'])
                self.assertTrue(case['arms'][arm]['group']['limited_scope_coverage']['complete'])

    def test_toolkit_test_module_is_accepted_only_for_source_without_changing_labels(self):
        with matplotlib_source_contract_fixture() as f:
            module='lib/mpl_toolkits/axes_grid1/tests/test_axes_grid1.py'
            labels={'f2p':[module+'::test_fix'], 'ptp':[module+'::test_old',module+'::test_old_too']}
            f.source_row['test_patch']='+++ b/'+module+'\nCPU_TEST_ONLY'
            for suite,field in [('f2p','FAIL_TO_PASS'),('ptp','PASS_TO_PASS')]:
                f.source_row[field]=json.dumps(labels[suite])
                f.c['cases'][0]['label_map'][suite]=[dict(published=x,node=x) for x in labels[suite]]
            with self.assertRaises(ValueError):r.mapped_labels('matplotlib/matplotlib',labels['f2p'])
            loaded=r.load_contract(f.path,write(f.path,f.c),f.output)
            self.assertEqual(loaded['cases'][0]['labels'],labels)
            self.assertEqual(r.resolve_matplotlib_nodes(module,'def test_fix(): pass\n',labels['f2p'],allow_mpl_toolkits=True),labels['f2p'])
            with self.assertRaises(ValueError):r.resolve_matplotlib_nodes(module,'def test_fix(): pass\n',labels['f2p'])

    def test_toolkit_source_rejects_unsafe_paths_and_unverified_parameter_escapes(self):
        bad=['lib/mpl_toolkits/../tests/test_x.py::test_x',
             'lib/mpl_toolkits/axes_grid1/tests/../../test_x.py::test_x',
             'lib/mpl_toolkits/axes_grid1/other/test_x.py::test_x',
             'lib/mpl_toolkits/axes_grid1/tests/conftest.py::test_x',
             '/lib/mpl_toolkits/axes_grid1/tests/test_x.py::test_x',
             'lib/matplotlib/tests/test_axes.py::test_errors[param\\(\\)',
             'lib/matplotlib/tests/test_axes.py::test_errors[\ninvalid]']
        for label in bad:
            with self.subTest(label=label),self.assertRaises(ValueError):
                r.mapped_labels('matplotlib/matplotlib',[label],allow_mpl_toolkits=True)

    def test_collection_admits_only_exact_or_unique_truncated_parameter_prefix(self):
        with matplotlib_source_collection_fixture() as f:
            f.collection['execution'].update(cleanup={'status':'ALREADY_REMOVED'},stdout_sha256=sha(f.collection_log),
                                               stderr_sha256=hashlib.sha256(b'').hexdigest(),seconds=1.0)
            f.c['node_collection']=reference(f.collection_path,f.collection)
            loaded=r.load_contract(f.path,write(f.path,f.c),f.output)
            self.assertEqual(loaded['cases'][0]['labels']['ptp'],[f.collection_ids[1]])
            self.assertEqual(loaded['cases'][0]['spec']['label_map']['ptp'][0]['published'],f.original['cases'][0]['label_map']['ptp'][0]['published'])
            self.assertFalse(f.output.exists())

    def test_collection_rejects_unexecuted_tampered_ambiguous_or_aliased_evidence(self):
        for edit in ('unexecuted','exit','cleanup','cleanup_conflict','stdout_conflict','wrong_source','wrong_base','changed_contract','changed_prior',
                     'changed_module','changed_log','ambiguous','duplicate_native','wrong_mapping','unmatched'):
            with self.subTest(edit=edit),matplotlib_source_collection_fixture() as f:
                if edit=='unexecuted':f.collection['execution']['container_started']=False
                elif edit=='exit':f.collection['execution']['exit']=1
                elif edit=='cleanup':f.collection['execution']['cleanup_status']='UNKNOWN'
                elif edit=='cleanup_conflict':f.collection['execution']['cleanup']={'status':'REMOVED_OWNED'}
                elif edit=='stdout_conflict':f.collection['execution']['stdout_sha256']='0'*64
                elif edit=='wrong_source':f.collection['instance_id']='matplotlib__matplotlib-90002'
                elif edit=='wrong_base':f.collection['base_commit']='0'*40
                elif edit=='changed_contract':Path(f.collection['source_contract']['path']).write_text('{}')
                elif edit=='changed_prior':Path(f.collection['qualification_receipt']['path']).write_text('{}')
                elif edit=='changed_module':f.collection_module.write_text('changed')
                elif edit=='changed_log':f.collection_log.write_text('changed')
                elif edit in ('ambiguous','duplicate_native','unmatched'):
                    nodes=list(f.collection_ids)
                    if edit=='ambiguous':nodes.append(f.collection_ids[1][:-1]+' other]')
                    elif edit=='duplicate_native':nodes.append(f.collection_ids[1])
                    else:nodes.remove(f.collection_ids[1])
                    f.collection_log.write_text('CONTEXTBENCH_COLLECTION='+json.dumps({'nodeids':nodes})+'\n')
                    f.collection['collection_log']['sha256']=sha(f.collection_log)
                else:f.c['cases'][0]['label_map']['ptp'][0]['node']='lib/matplotlib/tests/test_fake.py::unrelated'
                f.c['node_collection']=reference(f.collection_path,f.collection)
                with self.assertRaises(ValueError):r.load_contract(f.path,write(f.path,f.c),f.output)
                self.assertFalse(f.output.exists())

    def test_new_source_contract_uses_dataset_identity_without_pair_or_container(self):
        for instance_id in ('matplotlib__matplotlib-90001','matplotlib__matplotlib-90002'):
            with self.subTest(instance_id=instance_id),matplotlib_source_contract_fixture(instance_id) as f, \
                    mock.patch.object(subprocess,'Popen',side_effect=AssertionError('no container')):
                loaded=r.load_contract(f.path,f.sha,f.output)
                self.assertEqual(loaded['mode'],'matplotlib_source')
                self.assertEqual(loaded['cases'][0]['spec']['instance_id'],instance_id)
                self.assertEqual([len(loaded['cases'][0]['labels'][x]) for x in ('f2p','ptp')],[1,2])
                self.assertFalse(f.output.exists());f.assets['helper'].extract.assert_not_called()

    def test_source_identity_roles_labels_and_metadata_fail_closed(self):
        with matplotlib_source_contract_fixture() as f:
            for edit in ('role','source_id','revision','datafile','task','missing_ptp','empty_f2p','alias','metadata_repo','metadata_base','metadata_duplicate'):
                c=copy.deepcopy(f.c);meta=copy.deepcopy(f.source_meta)
                if edit=='role':c['cases'][0]['role']='target'
                elif edit=='source_id':c['cases'][0]['instance_id']='sympy__sympy-90001'
                elif edit=='revision':c['cases'][0]['base_commit']='0'*40
                elif edit=='datafile':c['cases'][0]['dataset_file']='SWEContextBench_Related_Lite.parquet'
                elif edit=='task':c['cases'][0]['problem_sha256']='0'*64
                elif edit=='missing_ptp':c['cases'][0]['label_map']['ptp'].pop()
                elif edit=='empty_f2p':c['cases'][0]['label_map']['f2p']=[]
                elif edit=='alias':c['cases'][0]['label_map']['f2p'][0]['node']=c['cases'][0]['label_map']['ptp'][0]['node']
                elif edit=='metadata_repo':meta['repo']='other/project'
                elif edit=='metadata_base':meta['base_commit']='0'*40
                f.shared.pq.read_table.return_value=SimpleNamespace(to_pylist=lambda:[meta,meta] if edit=='metadata_duplicate' else [meta])
                f.shared.pq.read_table.side_effect=None
                with self.subTest(edit=edit),self.assertRaises(ValueError):
                    r.load_contract(f.path,write(f.path,c),f.output)
            self.assertFalse(f.output.exists());f.assets['helper'].extract.assert_not_called()

    def test_optional_ast_mapping_requires_unique_bound_module_and_preserves_parameters(self):
        with matplotlib_source_contract_fixture() as f:
            module='lib/matplotlib/tests/test_other.py'
            node=f.c['cases'][0]['label_map']['ptp'][1]
            source=f.root/'public_tests.py';source.write_text('class TestPublic:\n def test_old_too(self): pass\n')
            f.c['cases'][0]['node_sources']={module:{'path':str(source),'sha256':sha(source)}}
            node['node']=module+'::TestPublic::test_old_too'
            loaded=r.load_contract(f.path,write(f.path,f.c),f.output)
            self.assertEqual(loaded['cases'][0]['labels']['ptp'][1],node['node'])
            bad=copy.deepcopy(f.c);bad['cases'][0]['label_map']['ptp'][1]['node']+='[invented]'
            with self.assertRaises(ValueError):r.load_contract(f.path,write(f.path,bad),f.output)
            source.write_text('class A:\n def test_old_too(self): pass\nclass B:\n def test_old_too(self): pass\n')
            f.c['cases'][0]['node_sources'][module]['sha256']=sha(source)
            with self.assertRaises(ValueError):r.load_contract(f.path,write(f.path,f.c),f.output)

    def test_ast_bound_module_is_rechecked_after_each_private_overlay(self):
        for changed in (False,True):
            with self.subTest(gold_changes_test=changed),matplotlib_source_contract_fixture() as f:
                module='lib/matplotlib/tests/test_other.py';code='class TestPublic:\n def test_old_too(self): pass\n'
                source=f.root/'public_tests.py';source.write_text(code)
                f.c['cases'][0]['node_sources']={module:{'path':str(source),'sha256':sha(source)}}
                f.c['cases'][0]['label_map']['ptp'][1]['node']=module+'::TestPublic::test_old_too'
                loaded=r.load_contract(f.path,write(f.path,f.c),f.output)
                def extract(_archive,base,_revision):
                    path=base/module;path.parent.mkdir(parents=True);path.write_text(code);return {}
                def apply_patch(work,content):
                    if changed and content==f.source_row['patch']:(work/module).write_text('changed by private gold')
                    return {'check_exit':0,'apply_exit':0}
                def group(work,labels,_runner,log,_assets,_slot,_timeout):
                    base=work.name=='base_with_tests'
                    record={'tests':{n:('failed' if base and 'test_fix' in n else 'passed') for n in labels},'fatal':[]}
                    log.write_text(r.MARKER+json.dumps(record)+'\n')
                    return dict(exit=1 if base else 0,result=record,log_sha256=sha(log),cleanup={'status':'ALREADY_REMOVED'},container_started=True)
                f.assets['helper'].extract.side_effect=extract;f.shared.apply_patch.side_effect=apply_patch
                with mock.patch.object(r,'mem_available',return_value=8*1024**3),mock.patch.object(r,'run_matplotlib_group',side_effect=group) as run:
                    result=r.execute(loaded)
                self.assertEqual(result['status'],'ERROR' if changed else 'QUALIFIED');self.assertEqual(run.call_count,1 if changed else 2)
                self.assertEqual((f.output/'registry.json').exists(),not changed)

    def test_source_qualification_emits_registry_only_for_complete_controls(self):
        for outcome in ('qualified','base_passes','base_ptp_fail','gold_skip','gold_error','gold_extra','cleanup_failure','not_started','cleanup_missing',
                        'input_changed_after_final_group','task_changed','testpatch_changed','log_changed'):
            with self.subTest(outcome=outcome),matplotlib_source_contract_fixture() as f:
                loaded=r.load_contract(f.path,f.sha,f.output)
                def extract(_archive,base,_revision):
                    base.mkdir();(base/'public.py').write_text('CPU_PUBLIC_BASE');return {}
                f.assets['helper'].extract.side_effect=extract
                def apply_patch(work,content):
                    (work/('test_overlay.txt' if content==f.source_row['test_patch'] else 'gold_overlay.txt')).write_text(content)
                    return {'check_exit':0,'apply_exit':0}
                f.shared.apply_patch.side_effect=apply_patch
                def group(work,labels,runner,log,_assets,_slot,_timeout):
                    base=work.name=='base_with_tests'
                    states={n:('failed' if base and 'test_fix' in n and outcome!='base_passes' else 'passed') for n in labels}
                    if base and outcome=='base_ptp_fail':states[labels[-1]]='failed'
                    if not base and outcome=='gold_skip':states[labels[-1]]='skipped'
                    if not base and outcome=='gold_error':states[labels[-1]]='error'
                    if not base and outcome=='gold_extra':states['UNREQUESTED']='passed'
                    record={'tests':states,'fatal':[]};log.write_text(r.MARKER+json.dumps(record)+'\n')
                    if not base and outcome=='input_changed_after_final_group':(f.data/'SWEContextBench_Lite_Experience.parquet').write_bytes(b'CHANGED')
                    if not base and outcome=='task_changed':(work.parent/'task.txt').write_text('CHANGED')
                    if not base and outcome=='testpatch_changed':(work.parent/'test.patch').write_text('CHANGED')
                    if not base and outcome=='log_changed':(work.parent/'base_with_tests.log').write_text('CHANGED')
                    returned=dict(exit=1 if 'failed' in states.values() else 0,result=record,
                                  log_sha256=sha(log),cleanup=dict(status='ALREADY_REMOVED'),container_started=True)
                    if not base and outcome=='cleanup_failure':returned['cleanup_error']={'type':'OWNED_FAKE'}
                    if not base and outcome=='not_started':returned['container_started']=False
                    if not base and outcome=='cleanup_missing':returned.pop('cleanup')
                    return returned
                with mock.patch.object(r,'mem_available',return_value=8*1024**3), \
                        mock.patch.object(r,'run_matplotlib_group',side_effect=group):
                    result=r.execute(loaded)
                registry=f.output/'registry.json';receipt=f.output/'receipt.json'
                self.assertEqual(result['status'],'QUALIFIED' if outcome=='qualified' else ('NOT_QUALIFIED' if outcome in ('base_passes','base_ptp_fail') else 'ERROR'))
                self.assertEqual(registry.exists(),outcome=='qualified');self.assertTrue(receipt.exists())
                clean=f.output/f.c['cases'][0]['instance_id']/'clean_base'
                self.assertFalse((clean/'test_overlay.txt').exists());self.assertFalse((clean/'gold_overlay.txt').exists())
                if outcome=='qualified':
                    value=json.loads(registry.read_text());case=result['cases'][f.c['cases'][0]['instance_id']]
                    self.assertEqual((result['role'],result['model_calls'],result['training']),('DEVELOPMENT_SOURCE',0,0))
                    self.assertEqual(set(value),{'schema','source_result','qualification_contract','actor_projection','rows'})
                    self.assertEqual(value['schema'],'qualified_matplotlib_development_source_v1')
                    self.assertEqual(value['source_result'],{'path':str(receipt),'sha256':sha(receipt)})
                    self.assertEqual(value['qualification_contract'],{'path':str(f.path),'sha256':f.sha})
                    self.assertEqual(value['actor_projection'],{'path':str(f.root/'projection'),'sha256':'a'*64})
                    self.assertEqual(value['rows'],[{'source':f.c['cases'][0]['instance_id'],'clean_base':str(clean)}])
                    self.assertEqual(case['clean_base_sha256'],r.tree(clean))
                    self.assertEqual(case['input_sha256']['task.txt'],f.c['cases'][0]['problem_sha256'])


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
