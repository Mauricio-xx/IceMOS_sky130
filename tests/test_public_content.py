"""Verify that intermediate commits remain subject to content review."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_checker_detects_content_removed_in_a_later_commit(tmp_path):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=tmp_path)
    git('init', '-q')
    git('config', 'user.name', 'Test')
    git('config', 'user.email', 'test@example.invalid')
    (tmp_path / 'baseline.txt').write_text('Synthetic baseline\n')
    git('add', '.')
    git('commit', '-qm', 'Baseline')
    base = git('rev-parse', 'HEAD').decode().strip()
    (tmp_path / 'example.txt').write_text('synthetic-restricted-marker\n')
    git('add', '.')
    git('commit', '-qm', 'Add synthetic marker')
    git('rm', '-q', 'example.txt')
    git('commit', '-qm', 'Remove synthetic marker')
    policy = tmp_path / 'local-policy.txt'
    policy.write_text('synthetic-restricted-marker\n')
    result = subprocess.run([sys.executable, str(ROOT / 'tools/check_public_content.py'),
                             '--base', base, '--deny-pattern-file', str(policy)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1
    assert 'example.txt' in result.stderr
    assert 'synthetic-restricted-marker' not in result.stderr
    result = subprocess.run([sys.executable, str(ROOT / 'tools/check_public_content.py'),
                             '--deny-pattern-file', str(policy)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0


def test_public_policy_accepts_spectre_syntax_and_rejects_other_model_names():
    import importlib.util
    spec = importlib.util.spec_from_file_location('public_checker', ROOT / 'tools/check_public_content.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    public = b'simulator lang=spectre\nmodel sky130_synthetic bsim4 type=n\n'
    assert checker.check_paths([('tests/synthetic.scs', public)], []) == []
    findings = checker.check_paths([('tests/synthetic.scs', public.replace(b'sky130_synthetic', b'external_model'))], [])
    assert len(findings) == 1 and 'SKY130 namespace' in findings[0]
