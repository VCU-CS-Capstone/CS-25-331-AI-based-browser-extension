// Utility to manage localStorage-backed project list
const projectSelect = document.getElementById("projectSelect");
const newProjectInput = document.getElementById("newProjectInput");
const createProjectBtn = document.getElementById("createProject");
const statusEl = document.getElementById("status");

function loadProjects() {
  const projects = JSON.parse(localStorage.getItem("projects") || "[]");
  projectSelect.innerHTML = "";
  projects.forEach(p => {
    const option = document.createElement("option");
    option.value = p;
    option.textContent = p;
    projectSelect.appendChild(option);
  });

  const selected = localStorage.getItem("selectedProject");
  if (selected && projects.includes(selected)) {
    projectSelect.value = selected;
  }
}

function saveProject(name) {
  const projects = new Set(JSON.parse(localStorage.getItem("projects") || "[]"));
  projects.add(name);
  localStorage.setItem("projects", JSON.stringify([...projects]));
  localStorage.setItem("selectedProject", name);
  loadProjects();
}

projectSelect.addEventListener("change", () => {
  const selected = projectSelect.value;
  localStorage.setItem("selectedProject", selected);
});

createProjectBtn.addEventListener("click", () => {
  const name = newProjectInput.value.trim();
  if (!name) return alert("Enter a project name.");
  saveProject(name);
  newProjectInput.value = "";
});

// Scrape & Send Embeddings
document.getElementById("scrapeAndSend").addEventListener("click", async () => {
  statusEl.textContent = "Status: Scraping...";
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => document.body.innerText
  }, async (results) => {
    const text = results[0].result;
    const url = tab.url;
    const project = projectSelect.value;

    try {
      const response = await fetch("http://127.0.0.1:8080/generate_embeddings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, url, project })
      });
      const data = await response.json();
      statusEl.textContent = "Status: " + data.message || "Success";
    } catch (err) {
      statusEl.textContent = "Status: Error - " + err.message;
    }
  });
});

// Ask a question
document.getElementById("askQuestion").addEventListener("click", async () => {
  const question = document.getElementById("questionInput").value.trim();
  const resultsDiv = document.getElementById("results");
  resultsDiv.innerHTML = "";

  if (!question) {
    resultsDiv.textContent = "Please enter a question.";
    return;
  }

  const project = projectSelect.value;

  try {
    const response = await fetch("http://127.0.0.1:8080/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, project })
    });

    const data = await response.json();
    if (data.matches && data.matches.length > 0) {
      const seen = new Set();
      data.matches.forEach(match => {
        if (seen.has(match.url)) return;
        seen.add(match.url);

        const link = document.createElement("a");
        link.href = match.url;
        link.textContent = `${match.url} (score: ${match.score})`;
        link.target = "_blank";

        const snippet = document.createElement("p");
        snippet.textContent = match.text;
        snippet.style.fontSize = "0.9em";

        resultsDiv.appendChild(link);
        resultsDiv.appendChild(snippet);
        resultsDiv.appendChild(document.createElement("hr"));
      });
    } else {
      resultsDiv.textContent = "No matching results found.";
    }
  } catch (err) {
    resultsDiv.textContent = "Error: " + err.message;
  }
});

loadProjects();
