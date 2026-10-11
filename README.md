# Smart Calendar

Advanced Higher Computing project. A command-line calendar that schedules your tasks around your fixed commitments.

## How it works

- Commitments have a fixed start and end, and can't overlap.
- Tasks have a due date, a duration and a difficulty from 1 to 5.
- Priority = (duration × difficulty) ÷ (days until due + 1)
- Tasks are sorted by priority, highest first, and each goes in the first gap between events long enough to fit it.
- Every change to the calendar reschedules all tasks.
- Data is stored in SQLite (`calendar.db`).

## Running it

```
python main.py
```

| Command | Action |
| --- | --- |
| `addc` | Add commitment |
| `addt` | Add task |
| `editc` | Edit commitment |
| `editt` | Edit task |
| `remove` | Remove event |
| `view` | View all events |
| `info` | Show commands and input formats |
| `quit` | Quit |

Dates use `YYYY-MM-DD hh:mm` and durations are in minutes. When editing, leave a field blank to keep it.
