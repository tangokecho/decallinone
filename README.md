# decallinone

PowerShell helper script that prints your LLM deployment checklist without triggering parser errors and optionally runs quick environment validations.

## Scripts

### `preflight.ps1`
Displays the assumptions, failure modes, and future enhancements you listed. Add `-RunValidations` to trigger basic checks for Python, NVIDIA/CUDA, and a running Ollama process. The script also includes helper functions for retrying operations, validating JSON, auto-creating directories, asserting non-empty responses, and writing files safely.

```powershell
pwsh ./preflight.ps1
pwsh ./preflight.ps1 -RunValidations -OutputDirectory "$HOME/llm-output"
```

The validation flag creates the output directory if it does not exist and writes a timestamped marker to `validation.txt` inside it.
