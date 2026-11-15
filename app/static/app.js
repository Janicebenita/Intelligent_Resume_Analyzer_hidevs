/* UI coordinates inputs and safe rendering; the Python engine owns every score. */
"use strict";
const byId = (id) => document.getElementById(id);
const state = { report: null, busy: false };
const controls = ["analyze-button", "load-demo", "import-file"];

function clearResult() {
  state.report = null;
  byId("report-output").hidden = true;
  byId("export-bar").hidden = true;
  byId("empty-state").hidden = false;
}

byId("analysis-form").addEventListener("input", () => {
  clearResult();
  byId("status").textContent = "Inputs changed. Run analysis to refresh the evidence.";
});

function setBusy(busy, message = "") {
  state.busy = busy;
  controls.forEach((id) => {
    byId(id).disabled = busy;
  });
  byId("analysis-form")
    .querySelectorAll("input, textarea, button")
    .forEach((control) => {
      control.disabled = busy;
    });
  byId("status").textContent = message;
  byId("error").hidden = true;
  byId("analysis-form").setAttribute("aria-busy", String(busy));
}

async function request(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new Error("Connection unavailable. Check your network and try again.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message || `Request failed (${response.status}). Try again.`);
  }
  return response;
}

function showError(error) {
  byId("error").textContent =
    error instanceof Error ? error.message : "The request could not finish.";
  byId("error").hidden = false;
}

function renderResult(result) {
  state.report = result.report;
  // HTML originates only from the server's autoescaped Jinja report template.
  byId("report-output").innerHTML = result.html;
  byId("empty-state").hidden = true;
  byId("report-output").hidden = false;
  byId("export-bar").hidden = false;
}

byId("load-demo").addEventListener("click", async () => {
  if (state.busy) return;
  clearResult();
  setBusy(true, "Loading the authored synthetic example…");
  try {
    const demo = await (await request("/api/demo")).json();
    byId("job-title").value = demo.job.title;
    byId("requirements").value = demo.job.requirements
      .map((r) => `${r.skill} | ${r.importance} | ${r.weight}`)
      .join("\n");
    byId("minimum-years").value = demo.job.minimum_years;
    byId("experience-weight").value = demo.job.experience_weight;
    byId("as-of").value = demo.as_of;
    byId("resume-text").value = demo.text;
    byId("resume-file").value = "";
    byId("file-name").textContent = "Synthetic text example loaded";
    setBusy(false, "Sample ready. Edit the rubric or select Analyze role alignment.");
  } catch (error) {
    setBusy(false);
    showError(error);
  }
});

byId("resume-file").addEventListener("change", () => {
  const file = byId("resume-file").files[0];
  byId("file-name").textContent = file ? file.name : "No document selected";
  if (file) byId("resume-text").value = "";
});

byId("analysis-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.busy) return;
  clearResult();
  setBusy(true, "Extracting document evidence and calculating the disclosed rubric…");
  try {
    const requirements = byId("requirements")
      .value.split("\n")
      .filter((line) => line.trim())
      .map((line, index) => {
        const parts = line.split("|").map((part) => part.trim());
        if (
          parts.length !== 3 ||
          !["required", "preferred"].includes(parts[1]) ||
          !/^([1-9]|10)$/.test(parts[2])
        ) {
          throw new Error(
            `Requirement line ${index + 1}: use skill | required or preferred | weight 1–10.`,
          );
        }
        return { skill: parts[0], importance: parts[1], weight: Number(parts[2]) };
      });
    const file = byId("resume-file").files[0];
    if (file && file.size > 2 * 1024 * 1024) throw new Error("Maximum resume file size is 2 MiB.");
    const data = new FormData();
    data.set(
      "job_json",
      JSON.stringify({
        title: byId("job-title").value,
        requirements,
        minimum_years: Number(byId("minimum-years").value),
        experience_weight: Number(byId("experience-weight").value),
      }),
    );
    data.set("as_of", byId("as-of").value);
    data.set("text", byId("resume-text").value);
    if (file) data.set("file", file);
    renderResult(await (await request("/api/analyze", { method: "POST", body: data })).json());
    setBusy(false, "Analysis ready. Review the evidence and parsing checks below.");
  } catch (error) {
    setBusy(false);
    showError(error);
  }
});

byId("import-file").addEventListener("change", async () => {
  const file = byId("import-file").files[0];
  if (!file || state.busy) return;
  setBusy(true, "Validating the saved JSON report and checking its score…");
  try {
    const data = new FormData();
    data.set("file", file);
    renderResult(await (await request("/api/import", { method: "POST", body: data })).json());
    setBusy(false, "Saved report opened. It retains its original analysis date and rubric.");
  } catch (error) {
    setBusy(false);
    showError(error);
  }
  byId("import-file").value = "";
});

document.querySelectorAll("[data-export]").forEach((button) =>
  button.addEventListener("click", async () => {
    if (!state.report || state.busy) return;
    setBusy(true, "Preparing your private report download…");
    try {
      const format = button.dataset.export;
      const response = await request("/api/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_json: JSON.stringify(state.report), format }),
      });
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `rolelens-${state.report.id.slice(0, 8)}.${format}`;
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      setBusy(
        false,
        format === "html"
          ? "Report downloaded. Open the HTML file and use your browser's Print / Save as PDF."
          : "Report downloaded. Store it privately.",
      );
    } catch (error) {
      setBusy(false);
      showError(error);
    }
  }),
);
