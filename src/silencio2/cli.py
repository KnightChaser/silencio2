# src/silencio2/cli.py
from __future__ import annotations

from pathlib import Path
import typer
from rich import print as rprint

from .store import load_inventory, save_inventory
from .badges import parse_badges
from .models import Inventory
from .redact import apply_redactions
from .unredact import unredact_text

app = typer.Typer(add_completion=False, help="Silencio2 CLI - Manage and redact sensitive information.")

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

    for code, desc, surface in parse_badges(lines):
        inv.add_or_merge(code=code, desc=desc, surface=surface)
        n_added += 1

    save_inventory(inv, inventory)
    rprint(f"[green]Success:[/green] Imported {n_added} badges into inventory '{inventory}'.")

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
        rprint(f"- [cyan]#{item.id}[/cyan] [bold]{item.code}[/bold]: {item.desc} ({item.surface}')")

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
