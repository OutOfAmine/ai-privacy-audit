const KEY = import.meta.env.VITE_OPENAI_KEY;
export async function ask(q) {
  const r = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST", headers: { Authorization: `Bearer ${KEY}` },
    body: JSON.stringify({ model: "gpt-4o", messages: [{ role: "user", content: q }] })
  });
  const j = await r.json();
  document.getElementById("out").innerHTML = j.choices[0].message.content;
}
