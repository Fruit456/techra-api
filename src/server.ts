import express from "express";

const app = express();
const port = process.env.PORT || 8080;

// Test-endpoint
app.get("/", (req, res) => {
  res.send("🚀 Techra API is running!");
});

// Placeholder för autentiserad användare (kommer från Entra/MSAL senare)
app.get("/me", (req, res) => {
  res.json({
    message: "Här kommer din användardata när vi kopplar Entra.",
    user: null
  });
});

app.listen(port, () => {
  console.log(`✅ Techra API listening on port ${port}`);
});
