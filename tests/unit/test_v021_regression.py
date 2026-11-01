from docsentry.contracts.docs import DocSpan
from docsentry.extractors.markdown import MarkdownExtractor
from docsentry.extractors.python_ast import compare_python_facts, extract_python_module_facts
from docsentry.rules.config_flags import detect_config_flag_drift
from docsentry.rules.symbols import detect_symbol_drift

# =====================================================================
# 1. Failure Mode 1: Imperative Procedural Documentation Claims
# =====================================================================

def test_fm1_imperative_procedural_doc_positive() -> None:
    """Imperative procedural directives with code guidance must be classified as procedural."""
    me = MarkdownExtractor()
    text = "To send JSON, explicitly serialize the string with `data=json.dumps(payload)`."
    spans = me.extract("docs/quickstart.md", text)
    assert len(spans) == 1
    assert spans[0].claim_type in ("active_assertion", "procedural_instruction")


def test_fm1_general_conceptual_doc_negative_control() -> None:
    """General descriptions without active directives must remain general_description."""
    me = MarkdownExtractor()
    text = "JSON is a language-independent data format widely supported on the web."
    spans = me.extract("docs/quickstart.md", text)
    assert len(spans) == 1
    assert spans[0].claim_type == "general_description"


# =====================================================================
# 2. Failure Mode 2: Typed Class Attributes (AnnAssign)
# =====================================================================

def test_fm2_typed_class_attribute_annassign_positive() -> None:
    """Class attributes defined with type annotations (AnnAssign) must be tracked."""
    before = """
class ConfigDict:
    orm_mode: bool = False
"""
    after = """
class ConfigDict:
    from_attributes: bool = False
"""
    facts = compare_python_facts("pydantic/main.py", before, after)
    attr_rem = [f for f in facts if f.member == "orm_mode"]
    assert len(attr_rem) == 1
    assert attr_rem[0].kind == "function_removed"
    assert attr_rem[0].qualified_name == "ConfigDict.orm_mode"


def test_fm2_typed_class_attribute_unchanged_negative_control() -> None:
    """Unchanged typed class attributes must produce no change facts."""
    code = """
class ConfigDict:
    orm_mode: bool = False
"""
    facts = compare_python_facts("pydantic/main.py", code, code)
    assert len(facts) == 0


# =====================================================================
# 3. Failure Mode 3: Class-Body Assignments (Assign Scope Guard)
# =====================================================================

def test_fm3_class_body_assignment_removal_positive() -> None:
    """Class-body assignments removed in head must be extracted as removed."""
    before = """
class Flask:
    json_encoder = json.JSONEncoder
"""
    after = """
class Flask:
    json_provider_class = None
"""
    facts = compare_python_facts("flask/app.py", before, after)
    attr_rem = [f for f in facts if f.member == "json_encoder"]
    assert len(attr_rem) == 1
    assert attr_rem[0].kind == "function_removed"
    assert attr_rem[0].symbol == "Flask.json_encoder"


def test_fm3_class_body_assignment_unchanged_negative_control() -> None:
    """Class assignments that remain identical produce no removal facts."""
    code = """
class Flask:
    json_encoder = json.JSONEncoder
"""
    facts = compare_python_facts("flask/app.py", code, code)
    assert len(facts) == 0


# =====================================================================
# 4. Failure Mode 4: Environment Variable Configuration Lookups
# =====================================================================

def test_fm4_os_environ_get_positive() -> None:
    """os.environ.get calls must be captured as configuration flags."""
    before = "env = os.environ.get('FLASK_ENV', 'production')\n"
    after = "env = 'production'\n"
    facts = compare_python_facts("flask/cli.py", before, after)
    flag_facts = [f for f in facts if f.member == "FLASK_ENV"]
    assert len(flag_facts) == 1
    assert flag_facts[0].kind == "config_flag_changed"
    assert flag_facts[0].before == "FLASK_ENV"
    assert flag_facts[0].after is None


def test_fm4_os_getenv_positive() -> None:
    """os.getenv calls must be captured as configuration flags."""
    before = "debug = os.getenv('APP_DEBUG', 'False')\n"
    after = "debug = 'False'\n"
    facts = compare_python_facts("app/config.py", before, after)
    flag_facts = [f for f in facts if f.member == "APP_DEBUG"]
    assert len(flag_facts) == 1
    assert flag_facts[0].kind == "config_flag_changed"


# =====================================================================
# 5. Adversarial Robustness Tests
# =====================================================================

def test_adv_internal_private_class_attribute_not_drifted() -> None:
    """Internal private attributes without documentation do not trigger false drift."""
    before = """
class Handler:
    _internal_cache: dict = {}
"""
    after = """
class Handler:
    _internal_cache = None
"""
    facts = compare_python_facts("app/handler.py", before, after)
    fact = facts[0]
    
    # Doc discusses something completely unrelated
    doc_span = DocSpan(
        span_id="s1",
        path="docs/guide.md",
        line_start=1,
        line_end=1,
        block_type="paragraph",
        text="The public Handler class processes incoming network requests.",
        raw_text="The public Handler class processes incoming network requests.",
        heading_path=["Guide"],
        inline_code=[],
        links=[],
        claim_type="active_assertion",
    )
    finding = detect_symbol_drift(fact, doc_span, "FIND-01")
    assert finding is None


def test_adv_env_var_in_comment_or_string_never_extracted() -> None:
    """Environment variables only mentioned in comments or docstrings are not extracted."""
    code = """
# Remember to check FLASK_ENV in production
def run():
    msg = "FLASK_ENV is not set here"
    return msg
"""
    facts = extract_python_module_facts("app.py", code)
    assert "FLASK_ENV" not in facts.cli_flags


def test_adv_unchanged_env_var_produces_no_facts() -> None:
    """Identical os.environ.get calls produce zero diff facts."""
    code = "port = os.environ.get('PORT', '8000')\n"
    facts = compare_python_facts("app.py", code, code)
    assert len(facts) == 0


def test_adv_procedural_doc_remains_correct_when_unrelated_code_changes() -> None:
    """Procedural documentation is not falsely flagged when an unrelated function changes."""
    before = "def unrelated():\n    return 1\n"
    after = "def unrelated():\n    return 2\n"
    facts = compare_python_facts("utils.py", before, after)
    
    doc_span = DocSpan(
        span_id="s1",
        path="docs/quickstart.md",
        line_start=3,
        line_end=3,
        block_type="paragraph",
        text="To send JSON, explicitly serialize the string with data=json.dumps(payload).",
        raw_text="To send JSON, explicitly serialize the string with `data=json.dumps(payload)`.",
        heading_path=["Quickstart"],
        inline_code=["data=json.dumps(payload)"],
        links=[],
        claim_type="active_assertion",
    )
    finding = detect_config_flag_drift(facts[0], doc_span, "FIND-02")
    assert finding is None
