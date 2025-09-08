const venom = require('venom-bot');
const axios = require('axios');

venom
  .create({
    session: 'botassistente',
    multidevice: true,
    headless: true,
    browserArgs: ['--no-sandbox', '--disable-setuid-sandbox', '--headless=new'], // usa o modo novo
    executablePath: '"C:\Program Files\Google\Chrome\Application\chrome.exe"' // caminho correto do Chrome
  })
  .then((client) => start(client))
  .catch((erro) => {
    console.error('Erro ao iniciar o bot:', erro);
  });

function start(client) {
  client.onMessage(async (message) => {
    if (message.body && !message.isGroupMsg) {
      console.log("📨 Mensagem recebida:", message.body);

      try {
        const resposta = await axios.post('http://10.30.0.48:5000/webhook', {
          numero: message.from,
          mensagem: message.body,
        });

        console.log("🤖 Resposta recebida do Flask:", resposta.data);

        await client.sendText(message.from, resposta.data.resposta);
      } catch (err) {
        console.error('❌ Erro ao responder mensagem:', err);
      }
    }
  });
}

