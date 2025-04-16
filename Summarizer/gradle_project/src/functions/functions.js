/**
 * Summarizes text using AI
 * @customfunction
 * @param {string} text The text to summarize
 * @param {string} format The format prompt
 * @param {number} temperature The randomness (0-1)
 * @param {string} model The AI model to use
 * @returns {string}
 */
async function GPT_SUMMARIZE(text, format, temperature, model) {
  try {
    const response = await fetchData(text, format, temperature);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    const data = await response.json();

    return data.summarized_text || "Error: No summary generated";
  } catch (error) {
    console.error("GPT_SUMMARIZE error:", error);
    return `Error: ${error.message}`;
  }
}
  