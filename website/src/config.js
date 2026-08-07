// config.js
// Centralized configuration for the SpaceX website.
// Modify these variables to easily update links across the entire site.

export const config = {
  // Replace with the actual bot client ID if it changes
  INVITE_URL: 'https://discord.com/oauth2/authorize?client_id=1505527456155570196&permissions=7389966261939254&integration_type=0&scope=bot',
  
  // Official Support Server
  SUPPORT_URL: 'https://discord.gg/xgHkpePc9J',
  
  // Top.gg Voting link
  TOPGG_URL: 'https://top.gg/bot/1505527456155570196',
  
  // You can point this to an external URL or keep it relative (e.g. /images/spacex-logo.png)
  // Ensure spacex-logo.png is placed in the public/images folder.
  LOGO_URL: '/images/spacex-logo.png',
  
  BOT_NAME: 'SpaceX',
};
