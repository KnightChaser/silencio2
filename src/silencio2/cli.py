# src/silencio2/cli.py
from __future__ import annotations

from pathlib import Path
import typer
from rich import print as rprint

from .store import load_inventory, save_inventory
from .badges import parse_badges, validate_badge_lines
from .models import Inventory
from .redact import apply_redactions
from .unredact import unredact_text

app = typer.Typer(add_completion=False, help="Silencio2 CLI - Manage and redact sensitive information.")

alias_app = typer.Typer(help="Manage aliases")
app.add_typer(alias_app, name="alias")

@app.command("autoredact")
def autoredact(
    policy_file: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to the redaction-policy prompt file (text)"
    ),
    src_dir: Path = typer.Option(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Source directory cotnaining (text) documents to be redacted."
    ),
    out_dir: Path = typer.Option(
        ...,
        exists=False,
        file_okay=False,
        dir_okay=True,
        writable=True,
        help="Output directory where redacted documents and updated inventory will be saved."
    ),
):
    """
    Automatically redact documents in SRC_DIR according to the policy in POLICY_FILE,
    update the inventory at INVENTORY_FILE, and save redacted documents and updated inventory to OUT_DIR.
    """
    # Validate policy file is a text file
    try:
        policy_text = policy_file.read_text(encoding="utf-8")
    except Exception as e:
        rprint(f"[red]Error reading policy file:[/red] {e}")
        raise typer.Exit(code=1)

    # Verify source directory
    if not src_dir.is_dir():
        rprint(f"[red]Source directory does not exist or is not a directory:[/red] {src_dir}")
        raise typer.Exit(code=1)

    # Ensure output directory-create if missing
    try:
        out_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        rprint(f"[red]Output directory already exists:[/red] {out_dir}")
        raise typer.Exit(code=1)

    # Create an inventory file
    inventory_file = out_dir / "inventory.json"
    inv = Inventory(items=[])
    save_inventory(inv, inventory_file)

    # Stub: Here you’d call LLM suggestion, update inventory, run redaction, etc.
    rprint(f"[green]Info:[/green] POLICY file: {policy_file}")
    rprint(f"[green]Info:[/green] SRC DIR: {src_dir}")
    rprint(f"[green]Info:[/green] OUT DIR: {out_dir}")
    rprint(f"[green]Info:[/green] INVENTORY file: {inventory_file}")

    # TODO: implement suggestion + inventory merge + redaction pipeline
    rprint("[yellow]Stub:[/yellow] autoredact logic not yet implemented.")

    raise typer.Exit(code=0)

@app.command()
def init(out: Path = typer.Option(Path("./silencio2.inventory.json"), help="Inventory path")):
    """
    Initialize a new inventory file.
    """
    if out.exists():
        rprint(f"[red]Error:[/red] Inventory file '{out}' already exists.")
        raise typer.Exit(code=0)

    inventory = Inventory(items=[])
    save_inventory(inventory, out)
    rprint(f"[green]Success:[/green] Created new inventory at '{out}'.")

@app.command()
def import_badges(
    badges: Path,
    inventory: Path = typer.Option(Path("./silencio2.inventory.json"), help="Inventory path")
):
    """
    From a text file containing badge codes, import them into the inventory.
    """
    inv = load_inventory(inventory)
    lines = badges.read_text(encoding="utf-8").splitlines()
    n_added = 0

    try:
        for code, desc, surface in parse_badges(lines):
            inv.add_or_merge(code=code, desc=desc, surface=surface)
            n_added += 1
    except ValueError as exc:
        # parse_badges already annotates with "Error parsing line N: ..."
        rprint(f"[red]Error importing badges from[/red] {badges}:\n  {exc}")
        raise typer.Exit(code=1)

    save_inventory(inv, inventory)
    rprint(f"[green]Success:[/green] Imported {n_added} badges into inventory '{inventory}'.")

@app.command("validate-badges")
def validate_badges_cmd(
    badges: Path
) -> None:
    """
    Validate a badge file for correct formatting.
    Fails on any invalid badge-line.
    """
    lines = badges.read_text(encoding="utf-8").splitlines()
    try:
        n_valid, n_skipped = validate_badge_lines(lines)
    except ValueError as e:
        rprint(f"[red]Error validating badges file '{badges}':[/red]\n  {e}")
        raise typer.Exit(code=1)

    rprint(f"[green]Success:[/green] Validated '{badges}': {n_valid} valid badge lines, {n_skipped} skipped.")
    raise typer.Exit(code=0)

@app.command()
def list_items(inventory: Path = typer.Option(Path("./silencio2.inventory.json"), help="Inventory path")):
    """
    List all items in the inventory.
    """
    inv = load_inventory(inventory)
    if not inv.items:
        rprint(f"[yellow]Warning:[/yellow] Inventory '{inventory}' is empty.")
        raise typer.Exit(code=0)
    for item in sorted(inv.items, key=lambda x: (x.code, x.surface)):
        if item.aliases:
            alias_note = "  (aliases: " + ", ".join(f"{a.id}:{a.surface}" for a in item.aliases) + ")"
        else:
            alias_note = ""
        rprint(f"- [cyan]#{item.id}[/cyan] [bold]{item.code}[/bold]: {item.desc} ({item.surface}){alias_note}")


@alias_app.command("add")
def alias_add(
    item_id: int,
    alias_surface: str,
    inventory: Path = typer.Option(Path("./silencio2.inventory.json"), help="Inventory path")
):
    """
    Add an alias surface to an existing item in the inventory.
    """
    inv = load_inventory(inventory)
    alias_id = inv.add_alias(item_id=item_id, alias_surface=alias_surface)
    save_inventory(inv, inventory)
    if alias_id == 0:
        rprint(f"[yellow]Alias already exists[/yellow] for #{item_id}: {alias_surface!r}")
    else:
        rprint(f"[green]Alias added[/green] to #{item_id} as id {alias_id}: {alias_surface!r}")

@alias_app.command("list")
def alias_list(
    item_id: int,
    inventory: Path = typer.Option(Path("./silencio2.inventory.json"), help="Inventory path")
):
    """
    List all aliases for an item in the inventory.
    """
    inv = load_inventory(inventory)
    item = inv.find(item_id)

    if not item:
        rprint(f"[red]Error:[/red] Item ID #{item_id} not found in inventory.")
        raise typer.Exit(2)
    if not item.aliases:
        rprint(f"[yellow]No aliases found[/yellow] for item #{item_id}.")
        return

    rprint(f"[bold]Aliases for #{item_id}[/bold] ({item.code} {item.desc}):")
    for alias in item.aliases:
        rprint(f"  - {alias}")

@app.command()
def redact(
    src_dir: Path,
    dst_dir: Path,
    inventory: Path = typer.Option(Path("./silencio2.inventory.json"), help="Inventory path"),
    overwrite: bool = typer.Option(False, help="Overwrite existing files in destination"),
):
    """
    Redact .md files from SRC_DIR and save to DST_DIR using the inventory.
    """

    if not src_dir.is_dir():
        rprint(f"[red]Not a directory:[/red] {src_dir}")
        raise typer.Exit(2)
    if dst_dir.exists():
        if not overwrite:
            rprint(f"[red]Destination exists:[/red] {dst_dir} (use --overwrite)")
            raise typer.Exit(2)
    dst_dir.mkdir(parents=True, exist_ok=True)

    inv = load_inventory(inventory)
    md_files = [p for p in src_dir.rglob("*.md") if p.is_file()]
    if not md_files:
        rprint("[yellow]No .md files found.[/yellow]")
        raise typer.Exit()

    total = 0
    for p in md_files:
        text = p.read_text(encoding="utf-8")
        red, matches = apply_redactions(text, inv)
        rel = p.relative_to(src_dir)
        outp = dst_dir / rel
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(red, encoding="utf-8")
        rprint(f"[green]Redacted[/green] {rel}  (+{len(matches)} matches)")
        total += len(matches)

    rprint(f"[bold]Done.[/bold] Total matches: {total}")

@app.command()
def unredact(
    src_dir: Path,
    dst_dir: Path,
    inventory: Path = typer.Option(Path("./silencio2.inventory.json"), help="Inventory path"),
    overwrite: bool = typer.Option(False, help="Overwrite existing files in destination"),
):
    """
    Unredact .md files from SRC_DIR and save to DST_DIR using the inventory.
    """

    if not src_dir.is_dir():
        rprint(f"[red]Not a directory:[/red] {src_dir}")
        raise typer.Exit(2)
    if dst_dir.exists():
        if not overwrite:
            rprint(f"[red]Destination exists:[/red] {dst_dir} (use --overwrite)")
            raise typer.Exit(2)
    dst_dir.mkdir(parents=True, exist_ok=True)

    inv = load_inventory(inventory)
    md_files = [p for p in src_dir.rglob("*.md") if p.is_file()]
    if not md_files:
        rprint("[yellow]No .md files found.[/yellow]")
        raise typer.Exit()

    for p in md_files:
        text = p.read_text(encoding="utf-8")
        unred = unredact_text(text, inv)
        rel = p.relative_to(src_dir)
        outp = dst_dir / rel
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(unred, encoding="utf-8")
        rprint(f"[green]Unredacted[/green] {rel}")

    rprint(f"[bold]Done.[/bold] Processed {len(md_files)} files and restored files are written to '{dst_dir}'.")
