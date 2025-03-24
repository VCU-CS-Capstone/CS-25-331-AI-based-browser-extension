document.getElementById("scrapeAndSend").addEventListener("click", async () => {
    const statusElement = document.getElementById("status");
    statusElement.textContent = "Scraping webpage content...";

    try {
        // Get the active tab and its URL
        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab || !tab.url) {
            throw new Error("No active tab or URL found.");
        }

        let pageUrl = tab.url;  // Extract URL
        console.log("Page URL:", pageUrl);

        // Inject script to scrape text
        let scrapedText = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => document.body.innerText // Extracts human-readable text
        });

        if (!scrapedText || !scrapedText[0] || !scrapedText[0].result) {
            throw new Error("Failed to scrape webpage content.");
        }

        let textContent = scrapedText[0].result;
        console.log("Scraped text:", textContent);

        statusElement.textContent = "Sending text and URL to server for embedding...";

        // Send the text + URL to the embedding server
        let response = await fetch("http://127.0.0.1:8080/generate_embeddings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: textContent, url: pageUrl }),  // Include URL
        });

        let result = await response.json();

        if (response.ok) {
            console.log("Chunks received from server:", result.chunks);
            statusElement.textContent = "Embeddings stored successfully!";
        } else {
            throw new Error(result.error || "Failed to process text.");
        }
    } catch (error) {
        console.error("Error:", error);
        statusElement.textContent = "Error: " + error.message;
    }
});

document.getElementById("askQuestion").addEventListener("click", async () => {
    const question = document.getElementById("questionInput").value.trim();
    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = "";

    if (!question) {
        resultsDiv.textContent = "Please enter a question.";
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8080/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question })
        });

        const data = await response.json();
        if (data.matches && data.matches.length > 0) {
            const seenUrls = new Set();
        
            data.matches.forEach(match => {
                if (seenUrls.has(match.url)) return;
                seenUrls.add(match.url);
            
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
            resultsDiv.textContent = "No matching information found.";
        }
    } catch (error) {
        resultsDiv.textContent = "Error: " + error.message;
    }
});
