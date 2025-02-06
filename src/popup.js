// Function to scrape and collect text content from the current tab
function scrapePageContent() {
    return new Promise((resolve, reject) => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            const tabId = tabs[0].id;

            chrome.scripting.executeScript(
                {
                    target: { tabId: tabId },
                    func: () => {
                        // Select all human-readable elements
                        const elements = document.querySelectorAll("p, h1, h2, h3, div, span");
                        const texts = [];

                        elements.forEach((el) => {
                            // Extract text, trim whitespace, and ignore empty content
                            const text = el.innerText.trim();
                            if (text) texts.push(text);
                        });

                        return texts.join(" ");
                    },
                },
                (results) => {
                    if (chrome.runtime.lastError) {
                        reject(chrome.runtime.lastError.message);
                    } else if (results && results[0] && results[0].result) {
                        resolve(results[0].result);
                    } else {
                        reject("Failed to scrape content.");
                    }
                }
            );
        });
    });
}

// Event listener to test scraping functionality
document.getElementById("testScrape").addEventListener("click", async () => {
    const statusElement = document.getElementById("status");
    statusElement.textContent = "Scraping the current page...";

    try {
        // Call the scrapePageContent function
        const pageText = await scrapePageContent();
        console.log("Scraped text content:", pageText);

        // Update the status
        statusElement.textContent = "Scraping completed! Check console for the text.";
    } catch (error) {
        console.error("Error during scraping:", error);
        statusElement.textContent = "Error scraping the page. Check console.";
    }
});
