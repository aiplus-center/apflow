"""
Scheduler CLI commands

Commands for managing the internal scheduler and interacting with scheduled tasks.

Usage:
    apflow scheduler start          # Start the internal scheduler
    apflow scheduler stop           # Stop the running scheduler
    apflow scheduler status         # Show scheduler status
    apflow scheduler list           # List scheduled tasks
    apflow scheduler trigger TASK   # Manually trigger a task
    apflow scheduler export-ical    # Export tasks as iCal
"""

import asyncio
import os
import sys
import signal
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from apflow.logger import get_logger

logger = get_logger(__name__)
console = Console()

app = typer.Typer(name="scheduler", help="Manage task scheduler")

# Default scheduler PID file location
DEFAULT_SCHEDULER_PID_FILE = Path.home() / ".aiperceivable" / "apflow-scheduler.pid"
DEFAULT_SCHEDULER_LOG_FILE = Path.home() / ".aiperceivable" / "apflow-scheduler.log"


def get_pid_file() -> Path:
    """Get scheduler PID file path"""
    pid_file = os.getenv("APFLOW_SCHEDULER_PID_FILE", str(DEFAULT_SCHEDULER_PID_FILE))
    pid_path = Path(pid_file)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    return pid_path


def get_log_file() -> Path:
    """Get scheduler log file path"""
    log_file = os.getenv("APFLOW_SCHEDULER_LOG_FILE", str(DEFAULT_SCHEDULER_LOG_FILE))
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def read_pid() -> Optional[int]:
    """Read PID from file"""
    pid_file = get_pid_file()
    if not pid_file.exists():
        return None

    try:
        with open(pid_file, "r") as f:
            pid_str = f.read().strip()
            return int(pid_str) if pid_str else None
    except (ValueError, IOError):
        return None


def write_pid(pid: int) -> None:
    """Write PID to file"""
    pid_file = get_pid_file()
    with open(pid_file, "w") as f:
        f.write(str(pid))


def remove_pid() -> None:
    """Remove PID file"""
    pid_file = get_pid_file()
    if pid_file.exists():
        pid_file.unlink()


def is_process_running(pid: int) -> bool:
    """Check if process is running"""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


@app.command("start")
def start(
    poll_interval: int = typer.Option(
        60, "--poll-interval", "-i", help="Seconds between checking for due tasks"
    ),
    max_concurrent: int = typer.Option(
        10, "--max-concurrent", "-c", help="Maximum concurrent task executions"
    ),
    user_id: Optional[str] = typer.Option(
        None, "--user-id", "-u", help="Only process tasks for this user"
    ),
    background: bool = typer.Option(
        False, "--background/--foreground", "-b", help="Run in background"
    ),
    timeout: int = typer.Option(3600, "--timeout", "-t", help="Default task timeout in seconds"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable DEBUG-level logging and show task execution details"
    ),
):
    """
    Start the internal scheduler.

    The scheduler polls the database for due tasks and executes them.
    Use --background to run as a daemon process.
    Use --verbose to show task execution results (id, name, status).

    Examples:
        apflow scheduler start
        apflow scheduler start --verbose
        apflow scheduler start --poll-interval 30 --max-concurrent 5
        apflow scheduler start --background
    """
    try:
        # Check if scheduler is already running
        existing_pid = read_pid()
        if existing_pid and is_process_running(existing_pid):
            console.print(f"[red]Scheduler is already running (PID: {existing_pid})[/red]")
            raise typer.Exit(1)
        elif existing_pid:
            # Stale PID file, remove it
            remove_pid()

        if background:
            # Start in background
            import subprocess

            log_file = get_log_file()
            python_exe = sys.executable

            # Build command
            cmd = [
                python_exe,
                "-m",
                "apflow.scheduler.internal",
                "--poll-interval",
                str(poll_interval),
                "--max-concurrent",
                str(max_concurrent),
                "--timeout",
                str(timeout),
            ]

            if user_id:
                cmd.extend(["--user-id", user_id])

            if verbose:
                cmd.append("--verbose")

            # Start background process
            with open(log_file, "a") as log:
                process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=log,
                    start_new_session=True,
                )

            write_pid(process.pid)
            console.print(f"[green]Scheduler started in background (PID: {process.pid})[/green]")
            console.print(f"Log file: {log_file}")

        else:
            # Run in foreground
            console.print("[blue]Starting scheduler in foreground...[/blue]")
            console.print(f"Poll interval: {poll_interval}s")
            console.print(f"Max concurrent: {max_concurrent}")
            if user_id:
                console.print(f"User ID filter: {user_id}")
            if verbose:
                console.print("Verbose: ON (showing task execution results)")
            console.print("[yellow]Press Ctrl+C to stop[/yellow]")

            # Import and run scheduler
            from apflow.scheduler import InternalScheduler
            from apflow.scheduler.base import SchedulerConfig, SchedulerState

            config = SchedulerConfig(
                poll_interval=poll_interval,
                max_concurrent_tasks=max_concurrent,
                task_timeout=timeout,
                user_id=user_id,
            )

            scheduler = InternalScheduler(config, verbose=verbose)

            async def run():
                try:
                    await scheduler.start()
                    # Keep running until stopped
                    while scheduler.stats.state in (SchedulerState.running, SchedulerState.paused):
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    pass
                finally:
                    if scheduler.stats.state != SchedulerState.stopped:
                        await scheduler.stop()

            # Handle signals
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            def signal_handler():
                console.print("\n[yellow]Shutting down scheduler...[/yellow]")
                asyncio.create_task(scheduler.stop())

            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, signal_handler)
                except NotImplementedError:
                    # Windows doesn't support add_signal_handler
                    pass

            try:
                loop.run_until_complete(run())
            finally:
                loop.close()

            console.print("[green]Scheduler stopped[/green]")

    except Exception as e:
        console.print(f"[red]Error starting scheduler: {e}[/red]")
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command("stop")
def stop():
    """
    Stop the running scheduler.

    Sends SIGTERM to the background scheduler process.
    """
    try:
        pid = read_pid()
        if not pid:
            console.print("[yellow]No scheduler is running[/yellow]")
            return

        if not is_process_running(pid):
            console.print("[yellow]Scheduler process not found (stale PID file)[/yellow]")
            remove_pid()
            return

        # Send SIGTERM
        console.print(f"Stopping scheduler (PID: {pid})...")
        os.kill(pid, signal.SIGTERM)

        # Wait for process to stop
        import time

        for _ in range(30):  # Wait up to 30 seconds
            if not is_process_running(pid):
                break
            time.sleep(1)

        if is_process_running(pid):
            console.print("[yellow]Process did not stop gracefully, sending SIGKILL...[/yellow]")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)

        remove_pid()
        console.print("[green]Scheduler stopped[/green]")

    except Exception as e:
        console.print(f"[red]Error stopping scheduler: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
def status():
    """
    Show scheduler status.

    Displays whether the scheduler is running and its statistics.
    """
    try:
        pid = read_pid()

        table = Table(title="Scheduler Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        if pid and is_process_running(pid):
            table.add_row("Status", "[green]Running[/green]")
            table.add_row("PID", str(pid))
        elif pid:
            table.add_row("Status", "[yellow]Stale (process not found)[/yellow]")
            table.add_row("PID (stale)", str(pid))
        else:
            table.add_row("Status", "[red]Not running[/red]")

        table.add_row("PID file", str(get_pid_file()))
        table.add_row("Log file", str(get_log_file()))

        console.print(table)

        # Try to get more detailed stats via API if available
        try:
            # TODO: Implement stats endpoint
            pass
        except Exception:
            pass

    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")
        raise typer.Exit(1)


@app.command("trigger")
def trigger(
    task_id: str = typer.Argument(..., help="Task ID to trigger"),
    wait: bool = typer.Option(False, "--wait", "-w", help="Wait for task completion"),
):
    """
    Manually trigger a scheduled task.

    Executes the task immediately regardless of its schedule.

    Examples:
        apflow scheduler trigger abc123
        apflow scheduler trigger abc123 --wait
    """
    try:
        console.print(f"Triggering task: {task_id}")

        async def run_trigger():
            from apflow.scheduler.gateway import WebhookGateway

            gateway = WebhookGateway()
            result = await gateway.trigger_task(task_id, execute_async=not wait)
            return result

        result = asyncio.run(run_trigger())

        if result.get("success"):
            console.print("[green]Task triggered successfully[/green]")
            if result.get("status"):
                console.print(f"Status: {result['status']}")
            if result.get("result"):
                console.print(f"Result: {json.dumps(result['result'], indent=2)}")

            if not wait:
                console.print("\n[yellow]Task is executing in the background.[/yellow]")
                console.print(
                    "Use [cyan]apflow scheduler trigger <id> --wait[/cyan] to wait for completion."
                )
                console.print(
                    "Use [cyan]apflow scheduler list --status running[/cyan] to see running tasks."
                )
        else:
            console.print(f"[red]Failed to trigger task: {result.get('error')}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error triggering task: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_scheduled(
    enabled_only: bool = typer.Option(
        True, "--enabled-only/--all", help="Only show enabled schedules (default: enabled only)"
    ),
    user_id: Optional[str] = typer.Option(None, "--user-id", "-u", help="Filter by user ID"),
    schedule_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by schedule type (once, interval, cron, daily, weekly, monthly)",
    ),
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by task status (e.g. pending, running, completed, failed)",
    ),
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum number of tasks"),
    output_format: str = typer.Option(
        "table", "--format", "-f", help="Output format: json or table"
    ),
) -> None:
    """
    List all scheduled tasks.

    Shows tasks that have scheduling configured. Use this to monitor
    all scheduled tasks in the system, including those currently running.

    Examples:
        apflow scheduler list
        apflow scheduler list --all
        apflow scheduler list --type daily
        apflow scheduler list --status running
        apflow scheduler list -f json
    """
    try:
        from apflow.cli.api_gateway_helper import (
            get_api_client_if_configured,
            log_api_usage,
            run_async_safe,
            should_use_api,
        )
        from apflow.core.config import get_task_model_class
        from apflow.core.storage import get_default_session
        from apflow.core.storage.sqlalchemy.task_repository import TaskRepository

        using_api = should_use_api()
        log_api_usage("scheduled.list", using_api)

        async def get_scheduled_tasks() -> list:
            async with get_api_client_if_configured() as client:
                if client:
                    return await client.call_method(
                        "tasks.scheduled.list",
                        enabled_only=enabled_only,
                        user_id=user_id,
                        schedule_type=schedule_type,
                        status=status,
                        limit=limit,
                    )

            db_session = get_default_session()
            task_repository = TaskRepository(
                db_session,
                task_model_class=get_task_model_class(),
            )

            tasks = await task_repository.get_scheduled_tasks(
                enabled_only=enabled_only,
                user_id=user_id,
                schedule_type=schedule_type,
                status=status,
                limit=limit,
            )

            return [task.output() for task in tasks]

        tasks = run_async_safe(get_scheduled_tasks())

        if output_format == "json":
            console.print(json.dumps(tasks, indent=2))
        else:
            from apflow.cli.commands.tasks import _print_scheduled_tasks_table

            _print_scheduled_tasks_table(tasks)

    except Exception as e:
        console.print(f"[red]Error listing scheduled tasks: {e}[/red]")
        logger.error(f"Failed to list scheduled tasks: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command("export-ical")
def export_ical(
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path (default: stdout)"
    ),
    user_id: Optional[str] = typer.Option(None, "--user-id", "-u", help="Filter by user ID"),
    schedule_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Filter by schedule type"
    ),
    calendar_name: str = typer.Option("APFlow Tasks", "--name", "-n", help="Calendar name"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Base URL for task links"),
    enabled_only: bool = typer.Option(
        True, "--enabled-only/--all", help="Only include enabled schedules"
    ),
):
    """
    Export scheduled tasks as iCalendar file.

    The output can be imported into calendar applications like Google Calendar,
    Apple Calendar, Outlook, etc.

    Examples:
        apflow scheduler export-ical
        apflow scheduler export-ical -o schedule.ics
        apflow scheduler export-ical --user-id user123 -o user_schedule.ics
    """
    try:
        console.print("Exporting scheduled tasks to iCal format...")

        async def run_export():
            from apflow.scheduler.gateway import ICalExporter

            exporter = ICalExporter(
                calendar_name=calendar_name,
                base_url=base_url,
            )

            ical_content = await exporter.export_tasks(
                user_id=user_id,
                schedule_type=schedule_type,
                enabled_only=enabled_only,
            )

            return ical_content

        ical_content = asyncio.run(run_export())

        if output:
            with open(output, "w") as f:
                f.write(ical_content)
            console.print(f"[green]Exported to: {output}[/green]")
        else:
            # Print to stdout
            print(ical_content)

    except Exception as e:
        console.print(f"[red]Error exporting iCal: {e}[/red]")
        logger.error(f"Failed to export iCal: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command("webhook-url")
def webhook_url(
    task_id: str = typer.Argument(..., help="Task ID"),
    base_url: str = typer.Option("http://localhost:8000", "--base-url", "-b", help="API base URL"),
):
    """
    Generate webhook URL for a task.

    The URL can be used to configure external schedulers (cron, K8s, etc.)
    to trigger task execution.

    Examples:
        apflow scheduler webhook-url abc123
        apflow scheduler webhook-url abc123 --base-url https://api.example.com
    """
    try:
        from apflow.scheduler.gateway import WebhookGateway

        gateway = WebhookGateway()
        url_info = gateway.generate_webhook_url(task_id, base_url)

        table = Table(title="Webhook Configuration")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("URL", url_info["url"])
        table.add_row("Method", url_info["method"])

        console.print(table)

        console.print("\n[blue]Example cron entry:[/blue]")
        console.print(f"  */5 * * * * curl -X POST {url_info['url']}")

    except Exception as e:
        console.print(f"[red]Error generating webhook URL: {e}[/red]")
        raise typer.Exit(1)


# Module entry point for background execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="APFlow Internal Scheduler")
    parser.add_argument("--poll-interval", type=int, default=60)
    parser.add_argument("--max-concurrent", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--user-id", type=str, default=None)
    parser.add_argument("--verbose", action="store_true", default=False)

    args = parser.parse_args()

    from apflow.scheduler.base import SchedulerConfig

    config = SchedulerConfig(
        poll_interval=args.poll_interval,
        max_concurrent_tasks=args.max_concurrent,
        task_timeout=args.timeout,
        user_id=args.user_id,
    )

    from apflow.scheduler.internal import run_scheduler

    asyncio.run(run_scheduler(config, verbose=args.verbose))
