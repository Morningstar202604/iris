"""Interactive messaging-platform setup wizards: WhatsApp (bridge + Cloud API), Slack manifest,
Skill Sync.

Split out of ``hermes_cli/main.py``. Names that still live in main are imported lazily at call time.
"""

import contextlib
import shutil
import subprocess
import sys

from hermes_cli.cli_output import line_input
from hermes_cli.model_setup_flows_common import _say


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _yes_no(prompt: str) -> bool:
    """``[y/N]`` prompt; Ctrl-C/EOF counts as "no"."""
    try:
        response = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        response = "n"
    return response.lower() in {"y", "yes"}


def _sync_device(args, ssc) -> int:
    name = getattr(args, "device_name", None)
    if name is not None:
        try:
            stored = ssc.set_device_name(name)
        except ValueError as e:
            _err(f"error: {e}")
            return 1
        print(f"device label set to '{stored}'.")
        _err("New commits from this device will use this label; existing commits keep their previous one.")
        return 0
    # No --name: print the current (creating a default on first use).
    print(ssc.stable_device_id())
    return 0


def _sync_propose(args, ssc) -> int:
    from tools.skills_sync_client_org import propose_skill
    name = args.name
    try:
        result = propose_skill(name, message=args.message)
    except ssc.SyncInertError as e:
        _err(f"cannot share this skill: {e}")
        return 1
    except ssc.SyncError as e:
        _err(f"could not share '{name}': {e}")
        return 1
    if result.get("proposal_pending"):
        print(f"Shared '{name}' with your organisation — an admin needs to "
              f"approve it (proposal #{result.get('proposal_id')}). It is "
              f"not live for the team until then.")
    else:
        print(f"Added '{name}' to your organisation's shared skills.")
    return 0


def _sync_toggle(args, sub: str) -> int:
    from tools.skill_usage import set_sync, is_curation_eligible
    skill = args.skill
    if not is_curation_eligible(skill):
        _err(f"'{skill}' is not sync-eligible (bundled, hub-installed, "
             f"external, or not found). Only agent-created / user-authored "
             f"skills under ~/.hermes/skills/ can sync.")
        return 1
    set_sync(skill, sub == "enable")
    print(f"sync {'enabled' if sub == 'enable' else 'disabled'} for '{skill}'.")
    return 0


def _sync_status(ssc) -> int:
    import json as _json
    status = ssc.sync_status()
    print(_json.dumps(status, indent=2, ensure_ascii=False))
    if status.get("org_available"):
        n = len(status.get("org_skills") or [])
        modified = status.get("org_skills_modified") or []
        _err(f"\nOrg skills: {n} shared skill(s) from your organisation "
             f"(your role: {status.get('org_role')}). They load alongside "
             f"your own, labeled by origin, and you can edit them.")
        if modified:
            _err(f"  {len(modified)} with local edits not yet shared: "
                 f"{', '.join(modified)}\n"
                 f"  Share them back with `hermes sync propose <skill>`. "
                 f"Org updates will not overwrite them.")
    elif status.get("logged_in"):
        _err("\nOrg skills: not applicable — this account isn't a member of a shared organisation.")
    if not status.get("logged_in"):
        _err("\nNot logged into Nous Portal — sync is inert.")
    elif not status.get("nous_admin"):
        _err("\nSync is not enabled for your account yet.")
    elif not status.get("feature_enabled"):
        _err("\nSync feature is off for this instance (set HERMES_SYNC_ENABLED=1 "
             "or config.yaml sync.enabled: true). Sync is inert.")
    elif not status.get("base_url"):
        _err("\nNo sync base URL configured (config.yaml sync.base_url or HERMES_SYNC_BASE_URL). Sync is inert.")
    return 0


def _sync_pull(ssc, identity):
    result = ssc.pull_skills(identity=identity)
    # Refresh the org mirror too when this account belongs to an organisation (no-op
    # otherwise), so one pull covers both.
    from tools.skills_sync_client_org import maybe_pull_org_skills
    org_result = maybe_pull_org_skills()
    if org_result:
        n = len(org_result.get("updated") or [])
        _err(f"org: refreshed {n} shared skill(s) from your organisation.")
        clashes = org_result.get("conflicted") or []
        if clashes:
            _err(f"org: {len(clashes)} skill(s) have BOTH local edits "
                 f"and org updates, so they were left as-is: "
                 f"{', '.join(clashes)}\n"
                 f"     Your local version is intact. Review it, then "
                 f"either propose it or delete the local copy and pull "
                 f"again to take the org version.")
    return result


# gated (identity-checked) sync subcommands: name -> (ssc, identity) -> result
_SYNC_GATED = {
    "pull": _sync_pull,
    "push": lambda ssc, identity: ssc.push_skills(identity=identity, message="hermes sync push"),
    "now": lambda ssc, identity: {"pull": ssc.pull_skills(identity=identity),
                                  "push": ssc.push_skills(identity=identity, message="hermes sync now")}}


def cmd_sync(args):
    """Skill Sync — personal sync across devices, plus sharing with your org."""
    import json as _json
    sub = getattr(args, "sync_command", None)
    if sub in {None, ""}:
        _err(_SYNC_USAGE)
        return 1
    if sub in {"enable", "disable"}:
        return _sync_toggle(args, sub)

    from tools import skills_sync_client as ssc
    if sub == "device":
        return _sync_device(args, ssc)
    if sub == "propose":
        return _sync_propose(args, ssc)
    if sub == "status":
        return _sync_status(ssc)

    # pull / push / now — enforce the gate up front with a clear message.
    try:
        identity = ssc.resolve_identity()
    except ssc.SyncInertError as e:
        _err(f"sync inert: {e}")
        return 1
    if not identity.get("nous_admin"):
        _err("sync unavailable: not enabled for your account yet.")
        return 1
    if not ssc.resolve_sync_base_url():
        _err("sync inert: no sync base URL configured (config.yaml sync.base_url or HERMES_SYNC_BASE_URL).")
        return 1

    action = _SYNC_GATED.get(sub)
    if action is None:
        _err(f"Unknown sync subcommand: {sub}")
        return 1
    try:
        result = action(ssc, identity)
    except ssc.SyncError as e:
        _err(f"sync failed: {e}")
        return 1
    print(_json.dumps(result, indent=2, ensure_ascii=False))
    return 0

