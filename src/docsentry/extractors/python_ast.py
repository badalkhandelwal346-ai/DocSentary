import ast
from typing import Any

from docsentry.contracts.code import CodeFact


class FunctionSignature:
    def __init__(
        self,
        name: str,
        qualified_name: str,
        line_start: int,
        line_end: int,
        parameters: list[dict[str, Any]],
        decorators: list[str],
        returns: str | None = None,
        is_overload: bool = False,
        is_async: bool = False,
        return_expressions: list[str] | None = None,
        raised_exceptions: list[str] | None = None,
        auth_required: bool = False,
    ) -> None:
        self.name = name
        self.qualified_name = qualified_name
        self.line_start = line_start
        self.line_end = line_end
        self.parameters = parameters
        self.decorators = decorators
        self.returns = returns
        self.is_overload = is_overload
        self.is_async = is_async
        self.return_expressions = return_expressions or []
        self.raised_exceptions = raised_exceptions or []
        self.auth_required = auth_required


class ModuleFacts:
    def __init__(self, path: str) -> None:
        self.path = path
        self.functions: dict[str, FunctionSignature] = {}
        self.classes: dict[str, int] = {}  # qualified_name -> line
        self.constants: dict[str, tuple[str, int]] = {}  # name -> (normalized_value, line)
        self.constant_param_links: dict[str, list[str]] = {}  # const_name -> [param_names]
        self.cli_flags: dict[str, tuple[str, int]] = {}  # flag -> (default_value, line)
        self.aliases: dict[str, str] = {}  # alias_name -> original_name
        self.all_exports: set[str] = set()
        self.imports: set[str] = set()
        # qualified_name -> (val, line)
        self.class_attributes: dict[str, tuple[str | None, int]] = {}
        self.dynamic_signals: list[tuple[str, str, int]] = []  # (symbol, reason, line)
        self.parse_warnings: list[str] = []


def _unparse_node(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


class ASTVisitor(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.scope_stack: list[str] = []
        self.facts = ModuleFacts(path)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qname = ".".join(self.scope_stack + [node.name])
        self.facts.classes[qname] = node.lineno
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record_function(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.facts.imports.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.facts.imports.add(alias.asname or alias.name)
        self.generic_visit(node)

    def _record_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qname_parts = self.scope_stack + [node.name]
        qualified_name = ".".join(qname_parts)

        params: list[dict[str, Any]] = []

        # Positional-only args
        posonly = getattr(node.args, "posonlyargs", [])
        num_defaults = len(node.args.defaults)
        all_regular = posonly + node.args.args
        default_offset = len(all_regular) - num_defaults

        for idx, arg in enumerate(all_regular):
            default_val = None
            if idx >= default_offset:
                def_node = node.args.defaults[idx - default_offset]
                default_val = _unparse_node(def_node)
                if isinstance(def_node, ast.Name):
                    self.facts.constant_param_links.setdefault(def_node.id, []).append(arg.arg)
                    self.facts.constant_param_links.setdefault(def_node.id, []).append(node.name)
                    if self.scope_stack:
                        self.facts.constant_param_links.setdefault(
                            def_node.id, []
                        ).append(self.scope_stack[-1])
                elif isinstance(def_node, ast.Call):
                    self.facts.dynamic_signals.append(
                        (node.name, "dynamic_default_call", node.lineno)
                    )
            kind = "POSITIONAL_ONLY" if idx < len(posonly) else "POSITIONAL_OR_KEYWORD"
            params.append(
                {
                    "name": arg.arg,
                    "kind": kind,
                    "default": default_val,
                    "annotation": _unparse_node(arg.annotation),
                }
            )

        # Vararg (*args)
        if node.args.vararg:
            params.append(
                {
                    "name": f"*{node.args.vararg.arg}",
                    "kind": "VAR_POSITIONAL",
                    "default": None,
                }
            )

        # Keyword-only args
        for arg, def_node in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=False):
            def_str = _unparse_node(def_node)
            if isinstance(def_node, ast.Name):
                self.facts.constant_param_links.setdefault(def_node.id, []).append(arg.arg)
                self.facts.constant_param_links.setdefault(def_node.id, []).append(node.name)
                if self.scope_stack:
                    self.facts.constant_param_links.setdefault(
                        def_node.id, []
                    ).append(self.scope_stack[-1])
            params.append(
                {
                    "name": arg.arg,
                    "kind": "KEYWORD_ONLY",
                    "default": def_str,
                    "annotation": _unparse_node(arg.annotation),
                }
            )

        # Kwarg (**kwargs)
        if node.args.kwarg:
            params.append(
                {
                    "name": f"**{node.args.kwarg.arg}",
                    "kind": "VAR_KEYWORD",
                    "default": None,
                }
            )

        decorators = [_unparse_node(d) or "" for d in node.decorator_list]
        is_overload = any("overload" in d for d in decorators)
        returns = _unparse_node(node.returns)

        # Inspect body for conditional defaults, dynamic dispatch, returns, and raises
        return_expressions: list[str] = []
        raised_exceptions: list[str] = []
        for n in ast.walk(node):
            if isinstance(n, ast.Return) and n.value is not None:
                # Track literal/data-structure returns or type constructors
                if isinstance(n.value, (ast.Constant, ast.List, ast.Dict, ast.Tuple, ast.Set)):
                    unp = _unparse_node(n.value)
                    if unp and unp not in return_expressions:
                        return_expressions.append(unp)
            elif isinstance(n, ast.Raise) and n.exc is not None:
                exc_node = n.exc.func if isinstance(n.exc, ast.Call) else n.exc
                unp = _unparse_node(exc_node)
                if unp and unp not in raised_exceptions:
                    raised_exceptions.append(unp)

        for stmt in node.body:
            if isinstance(stmt, ast.If):
                # if param is None: param = ...
                if isinstance(stmt.test, ast.Compare):
                    self.facts.dynamic_signals.append(
                        (node.name, "conditional_default_body", stmt.lineno)
                    )
            elif isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                if isinstance(stmt.value.func, ast.Name) and stmt.value.func.id == "getattr":
                    self.facts.dynamic_signals.append(
                        (node.name, "dynamic_dispatch_getattr", stmt.lineno)
                    )

        auth_required = any(
            any(kw in d.lower() for kw in ["auth", "login", "permission"]) for d in decorators
        )
        is_async = isinstance(node, ast.AsyncFunctionDef)

        sig = FunctionSignature(
            name=node.name,
            qualified_name=qualified_name,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            parameters=params,
            decorators=decorators,
            returns=returns,
            is_overload=is_overload,
            is_async=is_async,
            return_expressions=return_expressions,
            raised_exceptions=raised_exceptions,
            auth_required=auth_required,
        )

        # Only overwrite if not overload or no existing implementation
        if qualified_name not in self.facts.functions or not is_overload:
            self.facts.functions[qualified_name] = sig

        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        if not self.scope_stack:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id.isupper():
                        val = _unparse_node(node.value)
                        if val is not None:
                            self.facts.constants[target.id] = (val, node.lineno)
                    elif target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    self.facts.all_exports.add(elt.value)
                    elif isinstance(node.value, ast.Name):
                        # old_connect = new_connect
                        self.facts.aliases[target.id] = node.value.id
        else:
            cls_qname = ".".join(self.scope_stack)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    attr_qname = f"{cls_qname}.{target.id}"
                    val = _unparse_node(node.value)
                    self.facts.class_attributes[attr_qname] = (val, node.lineno)

        self._check_argparse(node.value, node.lineno)
        self._check_env_call(node.value, node.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name):
            val = _unparse_node(node.value)
            if not self.scope_stack:
                if node.target.id.isupper() and val is not None:
                    self.facts.constants[node.target.id] = (val, node.lineno)
            else:
                cls_qname = ".".join(self.scope_stack)
                attr_qname = f"{cls_qname}.{node.target.id}"
                self.facts.class_attributes[attr_qname] = (val, node.lineno)
        self._check_argparse(node.value, node.lineno)
        self._check_env_call(node.value, node.lineno)
        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> None:
        self._check_argparse(node.value, node.lineno)
        self._check_env_call(node.value, node.lineno)
        self.generic_visit(node)

    def _check_env_call(self, node: ast.AST | None, lineno: int) -> None:
        if node is None:
            return
        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                func_str = _unparse_node(n.func)
                if func_str in ("os.environ.get", "os.getenv") and n.args:
                    first_arg = n.args[0]
                    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                        flag_name = first_arg.value
                        def_val = _unparse_node(n.args[1]) if len(n.args) > 1 else "None"
                        self.facts.cli_flags[flag_name] = (def_val or "None", lineno)

    def _check_argparse(self, node: ast.AST, lineno: int) -> None:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "add_argument":
                flags = [ast.literal_eval(a) for a in node.args if isinstance(a, ast.Constant)]
                default_val = None
                for kw in node.keywords:
                    if kw.arg == "default":
                        default_val = _unparse_node(kw.value)
                for f in flags:
                    if isinstance(f, str) and f.startswith("-"):
                        self.facts.cli_flags[f] = (default_val or "None", lineno)


def extract_python_module_facts(path: str, source_code: str) -> ModuleFacts:
    visitor = ASTVisitor(path)
    try:
        tree = ast.parse(source_code, filename=path)
        visitor.visit(tree)
    except SyntaxError as err:
        visitor.facts.parse_warnings.append(f"SyntaxError in {path}:{err.lineno}: {err.msg}")
    except Exception as err:
        visitor.facts.parse_warnings.append(f"Parse error in {path}: {err}")
    return visitor.facts


def compare_python_facts(
    path: str,
    before_source: str | None,
    after_source: str | None,
    change_id: str = "diff",
) -> list[CodeFact]:
    facts: list[CodeFact] = []

    if before_source is None and after_source is None:
        return facts

    if before_source is None and after_source is not None:
        after_facts = extract_python_module_facts(path, after_source)
        for qname, sig in after_facts.functions.items():
            facts.append(
                CodeFact(
                    fact_id=f"func-add-{len(facts) + 1}",
                    language="python",
                    path=path,
                    qualified_name=qname,
                    symbol=sig.name,
                    kind="function_added",
                    after=sig.name,
                    line_after=sig.line_start,
                    source_change_id=change_id,
                    static_confidence="high",
                )
            )
        return facts

    if before_source is not None and after_source is None:
        before_facts = extract_python_module_facts(path, before_source)
        for qname, sig in before_facts.functions.items():
            facts.append(
                CodeFact(
                    fact_id=f"func-rem-{len(facts) + 1}",
                    language="python",
                    path=path,
                    qualified_name=qname,
                    symbol=sig.name,
                    kind="function_removed",
                    before=sig.name,
                    line_before=sig.line_start,
                    source_change_id=change_id,
                    static_confidence="high",
                )
            )
        return facts

    assert before_source is not None and after_source is not None
    before_facts = extract_python_module_facts(path, before_source)
    after_facts = extract_python_module_facts(path, after_source)

    for w in after_facts.parse_warnings:
        facts.append(
            CodeFact(
                fact_id=f"warn-{len(facts) + 1}",
                language="python",
                path=path,
                kind="parse_warning",
                after=w,
                source_change_id=change_id,
                static_confidence="high",
            )
        )

    # Record dynamic signals as low-confidence / ambiguous facts
    for sym, reason, line in after_facts.dynamic_signals:
        facts.append(
            CodeFact(
                fact_id=f"dyn-{len(facts) + 1}",
                language="python",
                path=path,
                symbol=sym,
                kind="parse_warning",
                after=f"Dynamic signal: {reason}",
                line_after=line,
                source_change_id=change_id,
                static_confidence="low",
                metadata={"dynamic": True, "reason": reason},
            )
        )

    all_after_func_symbols = [f.name for f in after_facts.functions.values()]

    # 1. Compare functions
    for qname, before_sig in before_facts.functions.items():
        if qname not in after_facts.functions:
            # Check if preserved by alias, export, or import
            if (
                before_sig.name in after_facts.aliases
                or before_sig.name in after_facts.all_exports
                or before_sig.name in after_facts.imports
            ):
                continue

            facts.append(
                CodeFact(
                    fact_id=f"func-rem-{len(facts) + 1}",
                    language="python",
                    path=path,
                    qualified_name=qname,
                    symbol=before_sig.name,
                    kind="function_removed",
                    before=before_sig.name,
                    line_before=before_sig.line_start,
                    source_change_id=change_id,
                    static_confidence="high",
                )
            )
            continue

        after_sig = after_facts.functions[qname]
        siblings = [s for s in all_after_func_symbols if s != after_sig.name]

        before_params = {p["name"]: p for p in before_sig.parameters}
        after_params = {p["name"]: p for p in after_sig.parameters}

        # Check default value changes
        for pname, b_param in before_params.items():
            if pname in after_params:
                a_param = after_params[pname]
                b_def = b_param.get("default")
                a_def = a_param.get("default")
                if b_def != a_def and (b_def is not None or a_def is not None):
                    facts.append(
                        CodeFact(
                            fact_id=f"default-chg-{len(facts) + 1}",
                            language="python",
                            path=path,
                            qualified_name=qname,
                            symbol=after_sig.name,
                            member=pname,
                            kind="default_changed",
                            before=str(b_def),
                            after=str(a_def),
                            line_before=before_sig.line_start,
                            line_after=after_sig.line_start,
                            source_change_id=change_id,
                            static_confidence="high",
                            metadata={"sibling_symbols": siblings},
                        )
                    )

        # Check removed parameters
        for pname in before_params:
            if pname not in after_params:
                facts.append(
                    CodeFact(
                        fact_id=f"param-rem-{len(facts) + 1}",
                        language="python",
                        path=path,
                        qualified_name=qname,
                        symbol=after_sig.name,
                        member=pname,
                        kind="parameter_removed",
                        before=pname,
                        line_before=before_sig.line_start,
                        line_after=after_sig.line_start,
                        source_change_id=change_id,
                        static_confidence="high",
                        metadata={"sibling_symbols": siblings},
                    )
                )

        # Check added parameters
        for pname in after_params:
            if pname not in before_params:
                facts.append(
                    CodeFact(
                        fact_id=f"param-add-{len(facts) + 1}",
                        language="python",
                        path=path,
                        qualified_name=qname,
                        symbol=after_sig.name,
                        member=pname,
                        kind="parameter_added",
                        after=pname,
                        line_before=before_sig.line_start,
                        line_after=after_sig.line_start,
                        source_change_id=change_id,
                        static_confidence="high",
                    )
                )

        # Check return value changes
        if before_sig.return_expressions != after_sig.return_expressions:
            b_ret = ", ".join(before_sig.return_expressions)
            a_ret = ", ".join(after_sig.return_expressions)
            if b_ret != a_ret:
                facts.append(
                    CodeFact(
                        fact_id=f"ret-chg-{len(facts) + 1}",
                        language="python",
                        path=path,
                        qualified_name=qname,
                        symbol=after_sig.name,
                        member="return",
                        kind="return_changed",
                        category="behavioral",
                        before=b_ret or "None",
                        after=a_ret or "None",
                        line_before=before_sig.line_start,
                        line_after=after_sig.line_start,
                        source_change_id=change_id,
                        static_confidence="medium",
                    )
                )

        # Check raised exception changes
        if before_sig.raised_exceptions != after_sig.raised_exceptions:
            b_exc = ", ".join(before_sig.raised_exceptions)
            a_exc = ", ".join(after_sig.raised_exceptions)
            if b_exc != a_exc:
                facts.append(
                    CodeFact(
                        fact_id=f"exc-chg-{len(facts) + 1}",
                        language="python",
                        path=path,
                        qualified_name=qname,
                        symbol=after_sig.name,
                        member="exception",
                        kind="exception_changed",
                        category="behavioral",
                        before=b_exc or "None",
                        after=a_exc or "None",
                        line_before=before_sig.line_start,
                        line_after=after_sig.line_start,
                        source_change_id=change_id,
                        static_confidence="medium",
                    )
                )

        # Check auth requirement change
        if before_sig.auth_required != after_sig.auth_required:
            facts.append(
                CodeFact(
                    fact_id=f"auth-chg-{len(facts) + 1}",
                    language="python",
                    path=path,
                    qualified_name=qname,
                    symbol=after_sig.name,
                    member="authentication",
                    kind="behavior_changed",
                    category="behavioral",
                    before="unauthenticated" if not before_sig.auth_required else "authenticated",
                    after="authenticated" if after_sig.auth_required else "unauthenticated",
                    line_before=before_sig.line_start,
                    line_after=after_sig.line_start,
                    source_change_id=change_id,
                    static_confidence="high",
                )
            )

        # Check sync to async change
        if before_sig.is_async != after_sig.is_async:
            facts.append(
                CodeFact(
                    fact_id=f"async-chg-{len(facts) + 1}",
                    language="python",
                    path=path,
                    qualified_name=qname,
                    symbol=after_sig.name,
                    member="async",
                    kind="behavior_changed",
                    category="behavioral",
                    before="sync" if not before_sig.is_async else "async",
                    after="async" if after_sig.is_async else "sync",
                    line_before=before_sig.line_start,
                    line_after=after_sig.line_start,
                    source_change_id=change_id,
                    static_confidence="high",
                )
            )

    # Compare classes
    for qname, line in before_facts.classes.items():
        if qname not in after_facts.classes:
            cls_name = qname.split(".")[-1]
            if cls_name in after_facts.aliases or cls_name in after_facts.all_exports:
                continue
            facts.append(
                CodeFact(
                    fact_id=f"cls-rem-{len(facts) + 1}",
                    language="python",
                    path=path,
                    qualified_name=qname,
                    symbol=cls_name,
                    kind="function_removed",
                    before=cls_name,
                    line_before=line,
                    source_change_id=change_id,
                    static_confidence="high",
                )
            )

    # 2. Compare Constants
    all_constants = list(after_facts.constants.keys())
    for cname, (b_val, b_line) in before_facts.constants.items():
        if cname in after_facts.constants:
            a_val, a_line = after_facts.constants[cname]
            if b_val != a_val:
                linked = after_facts.constant_param_links.get(cname, [])
                siblings = [c for c in all_constants if c != cname]
                facts.append(
                    CodeFact(
                        fact_id=f"const-chg-{len(facts) + 1}",
                        language="python",
                        path=path,
                        qualified_name=cname,
                        symbol=cname,
                        member=cname,
                        kind="constant_changed",
                        before=b_val,
                        after=a_val,
                        line_before=b_line,
                        line_after=a_line,
                        source_change_id=change_id,
                        static_confidence="high",
                        metadata={"linked_params": linked, "sibling_constants": siblings},
                    )
                )

    # 3. Compare CLI Flags
    for flag, (b_def, b_line) in before_facts.cli_flags.items():
        if flag not in after_facts.cli_flags:
            facts.append(
                CodeFact(
                    fact_id=f"flag-chg-{len(facts) + 1}",
                    language="python",
                    path=path,
                    symbol="argparse",
                    member=flag,
                    kind="config_flag_changed",
                    before=flag,
                    after=None,
                    line_before=b_line,
                    source_change_id=change_id,
                    static_confidence="high",
                )
            )
        else:
            a_def, a_line = after_facts.cli_flags[flag]
            if b_def != a_def:
                facts.append(
                    CodeFact(
                        fact_id=f"flag-chg-{len(facts) + 1}",
                        language="python",
                        path=path,
                        symbol="argparse",
                        member=flag,
                        kind="config_flag_changed",
                        before=b_def,
                        after=a_def,
                        line_before=b_line,
                        line_after=a_line,
                        source_change_id=change_id,
                        static_confidence="high",
                    )
                )

    # 4. Compare Class Attributes
    for attr_qname, (b_val, b_line) in before_facts.class_attributes.items():
        attr_name = attr_qname.split(".")[-1]
        cls_name = attr_qname.split(".")[0]
        if attr_qname not in after_facts.class_attributes:
            facts.append(
                CodeFact(
                    fact_id=f"attr-rem-{len(facts) + 1}",
                    language="python",
                    path=path,
                    qualified_name=attr_qname,
                    symbol=attr_qname,
                    member=attr_name,
                    kind="function_removed",
                    before=b_val or attr_name,
                    after=None,
                    line_before=b_line,
                    source_change_id=change_id,
                    static_confidence="high",
                    metadata={"class_name": cls_name, "attribute_name": attr_name},
                )
            )
        else:
            a_val, a_line = after_facts.class_attributes[attr_qname]
            if b_val != a_val:
                facts.append(
                    CodeFact(
                        fact_id=f"attr-chg-{len(facts) + 1}",
                        language="python",
                        path=path,
                        qualified_name=attr_qname,
                        symbol=attr_qname,
                        member=attr_name,
                        kind="default_changed",
                        before=b_val or "None",
                        after=a_val or "None",
                        line_before=b_line,
                        line_after=a_line,
                        source_change_id=change_id,
                        static_confidence="high",
                        metadata={"class_name": cls_name, "attribute_name": attr_name},
                    )
                )

    return facts
