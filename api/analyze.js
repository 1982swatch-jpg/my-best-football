export default async function handler(req, res) {
  try {
    const home = req.query.home || "";
    const away = req.query.away || "";
    const fixture = req.query.fixture || "";

    let url =
      "https://football-analyzer-briu.onrender.com/analyze?home=" +
      encodeURIComponent(home) +
      "&away=" +
      encodeURIComponent(away);

    if (fixture) {
      url += "&fixture=" + encodeURIComponent(fixture);
    }

    const r = await fetch(url);
    const text = await r.text();

    res.setHeader("Content-Type", "application/json; charset=utf-8");
    res.status(r.status).send(text);
  } catch (e) {
    res.status(500).json({
      error: "proxy_failed",
      message: String(e)
    });
  }
}