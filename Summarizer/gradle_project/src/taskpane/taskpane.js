/* global Office, Excel */

// Initialize Office.js
Office.onReady(() => {
  console.log("Excel Add-in ready.")
  
  // Check if the document is ready before setting up event listeners
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupEventListeners);
  } else {
    setupEventListeners();  
  }
})

function setupEventListeners() {
  // Handle Summarize Rows button click
  document.getElementById('summarizeButton').addEventListener('click', function() {
      processRows();
  });
}

async function processRows() {
  const headerRow = Number.parseInt(document.getElementById("headerRow").value)
  const formatPrompt = document.getElementById("formatPrompt").value
  const outputColumn = document.getElementById("outputColumn").value.trim().toUpperCase()
  const temperature = Number.parseFloat(document.getElementById("temperature").value)
  const topK = Number.parseInt(document.getElementById("topK").value)
  const topP = Number.parseFloat(document.getElementById("topP").value)

  const mode = document.querySelector("input[name='rowMode']:checked").value
  let rowStart, rowEnd

  if (mode === "auto") {
    rowStart = headerRow + 1
    rowEnd = rowStart + Number.parseInt(document.getElementById("autoRowCount").value) - 1
  } else {
    rowStart = Number.parseInt(document.getElementById("fixedStartRow").value)
    rowEnd = Number.parseInt(document.getElementById("fixedEndRow").value)
  }

  try {
    showLoading(true)
    await Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getActiveWorksheet()

      // Generate A to Z column letters
      const colLetters = Array.from({ length: 26 }, (_, i) => String.fromCharCode(65 + i))

      // Load all input data needed for prompt values
      const inputRange = sheet.getRange(`A${rowStart}:Z${rowEnd}`)
      inputRange.load("values")
      await context.sync()

      const inputValues = inputRange.values
      const results = []

      for (let i = 0; i < inputValues.length; i++) {
        const row = inputValues[i]
        let currentPrompt = formatPrompt

        // Replace all placeholders {{column}}
        let missingData = false
        currentPrompt = currentPrompt.replace(/{{(.*?)}}/g, (match, columnName) => {
          console.log(`Looking for column: "${columnName}"`);
          // Check if the column name exists in the colMap
          if (!colLetters.includes(columnName)) {
            missingData = true
            return `[MISSING]`
          } else {
            const colIndex = colLetters.indexOf(columnName)
            const cellValue = row[colIndex] || `[MISSING]` // Default to [MISSING] if empty
            return cellValue
          }
        })

        if (missingData) {
          results.push(["Error: Missing data in one or more columns"])
          continue
        }

        const response = await fetchData(currentPrompt, formatPrompt, temperature, topK, topP);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        const data = await response.json();
        
        results.push([data.summarized_text || `Error`])
      }

      // Write results to specified column
      const outputRange = sheet.getRange(`${outputColumn}${rowStart}:${outputColumn}${rowEnd}`)
      outputRange.values = results
      await context.sync()
    })
  } catch (error) {
    console.error("Error processing rows:", error)
  }
  finally {
    showLoading(false)
  }
}

function fetchData(currentPrompt, formatPrompt, temperature, topK, topP) {
  return fetch("http://localhost:5000/summarize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: currentPrompt,
      format: formatPrompt,
      temperature,
      topK: topK,
      topP: topP,
    }),
  });
}

function showLoading(isLoading) {
  let spinner = document.getElementById("loadingSpinner")
  if (!spinner) {
    spinner = document.createElement("div")
    spinner.id = "loadingSpinner"
    spinner.style.position = "fixed"
    spinner.style.top = "0"
    spinner.style.left = "0"
    spinner.style.width = "100vw"
    spinner.style.height = "100vh"
    spinner.style.backgroundColor = "rgba(255, 255, 255, 0.7)"
    spinner.style.display = "flex"
    spinner.style.alignItems = "center"
    spinner.style.justifyContent = "center"
    spinner.style.fontSize = "24px"
    spinner.style.zIndex = "9999"
    spinner.innerText = "⏳ Summarizing rows..."
    document.body.appendChild(spinner)
  }
  spinner.style.display = isLoading ? "flex" : "none"
}