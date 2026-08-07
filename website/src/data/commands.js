// commands.js
// Centralized list of all bot commands.
// You can edit this array to dynamically update the Commands page.

export const commandData = [
  // Moderation
  { name: 'ban', description: 'Ban a member from the server.', usage: '!!ban @user [reason]', category: 'Moderation', aliases: ['hackban'], popular: 2 },
  { name: 'unban', description: 'Unban a member from the server.', usage: '!!unban <user_id>', category: 'Moderation', aliases: [] },
  { name: 'kick', description: 'Kick a member from the server.', usage: '!!kick @user [reason]', category: 'Moderation', aliases: [] },
  { name: 'mute', description: 'Timeout/mute a member.', usage: '!!mute @user [duration]', category: 'Moderation', aliases: ['timeout'] },
  { name: 'unmute', description: 'Remove a timeout from a member.', usage: '!!unmute @user', category: 'Moderation', aliases: ['untimeout'] },
  { name: 'warn', description: 'Warn a member for breaking rules.', usage: '!!warn @user [reason]', category: 'Moderation', aliases: [], popular: 3 },
  { name: 'warnings', description: 'Check a member\'s warnings.', usage: '!!warnings @user', category: 'Moderation', aliases: ['warns'] },
  { name: 'delwarn', description: 'Delete a specific warning.', usage: '!!delwarn @user [warn_id]', category: 'Moderation', aliases: [] },
  { name: 'clearwarn', description: 'Clear all warnings of a user.', usage: '!!clearwarn @user', category: 'Moderation', aliases: [] },
  { name: 'purge', description: 'Delete multiple messages at once.', usage: '!!purge [amount]', category: 'Moderation', aliases: ['clear'] },
  { name: 'lock', description: 'Lock the current channel.', usage: '!!lock', category: 'Moderation', aliases: [] },
  { name: 'lockdown', description: 'Lock down the entire server.', usage: '!!lockdown', category: 'Moderation', aliases: [], popular: 2 },
  { name: 'slowmode', description: 'Set slowmode in a channel.', usage: '!!slowmode [seconds]', category: 'Moderation', aliases: ['sm'] },
  { name: 'poll', description: 'Create a yes/no poll.', usage: '!!poll [question]', category: 'Moderation', aliases: [] },
  { name: 'logs', description: 'Set up mod logs channel.', usage: '!!logs [channel]', category: 'Moderation', aliases: [] },
  { name: 'lookup', description: 'Lookup info about a user.', usage: '!!lookup @user', category: 'Moderation', aliases: [] },
  { name: 'pin', description: 'Pin a message in the channel.', usage: '!!pin [message_id]', category: 'Moderation', aliases: [] },
  { name: 'prefix', description: 'Change the bot prefix for this server.', usage: '!!prefix [new_prefix]', category: 'Moderation', aliases: [] },
  { name: 'roleaudit', description: 'Audit all roles in the server.', usage: '!!roleaudit', category: 'Moderation', aliases: [], popular: 3 },
  { name: 'say', description: 'Make the bot say a message.', usage: '!!say [message]', category: 'Moderation', aliases: [] },
  { name: 'staffstats', description: 'Check moderation stats for staff.', usage: '!!staffstats', category: 'Moderation', aliases: [] },
  
  // Giveaways
  { name: 'giveaway start', description: 'Start a new giveaway.', usage: '!!giveaway start [time] [winners] [prize]', category: 'Utility', aliases: ['gstart'] },
  { name: 'giveaway reroll', description: 'Reroll a giveaway winner.', usage: '!!giveaway reroll [message_id]', category: 'Utility', aliases: ['greroll'] },
  { name: 'giveaway end', description: 'End a giveaway early.', usage: '!!giveaway end [message_id]', category: 'Utility', aliases: ['gend'] },

  // Tickets
  { name: 'ticket setup', description: 'Setup the ticket panel in a channel.', usage: '!!ticket setup', category: 'Tickets', aliases: [] },
  { name: 'ticket add', description: 'Add a user to a ticket.', usage: '!!ticket add @user', category: 'Tickets', aliases: [] },
  { name: 'ticket remove', description: 'Remove a user from a ticket.', usage: '!!ticket remove @user', category: 'Tickets', aliases: [] },
  { name: 'ticket claim', description: 'Claim an open ticket.', usage: '!!ticket claim', category: 'Tickets', aliases: [] },
  { name: 'ticket close', description: 'Close a ticket and generate a transcript.', usage: '!!ticket close', category: 'Tickets', aliases: [] },
  { name: 'ticket transcript', description: 'Manually generate a transcript.', usage: '!!ticket transcript', category: 'Tickets', aliases: [] },
  { name: 'ticket rename', description: 'Rename a ticket channel.', usage: '!!ticket rename [name]', category: 'Tickets', aliases: [] },

  // Welcome
  { name: 'welcome setup', description: 'Configure welcome messages and channels.', usage: '!!welcome setup', category: 'Welcome', aliases: [] },
  { name: 'welcome test', description: 'Test the welcome message.', usage: '!!welcome test', category: 'Welcome', aliases: [] },

  // Economy & Stocks
  { name: 'bal', description: 'Check your wallet and bank balance.', usage: '!!bal [user]', category: 'Economy', aliases: ['balance'], popular: 2 },
  { name: 'bank deposit', description: 'Deposit coins to your bank.', usage: '!!bank deposit [amount]', category: 'Economy', aliases: ['dep'] },
  { name: 'bank withdraw', description: 'Withdraw coins from your bank.', usage: '!!bank withdraw [amount]', category: 'Economy', aliases: ['with'] },
  { name: 'work', description: 'Work a job to earn some coins.', usage: '!!work', category: 'Economy', aliases: [], popular: 1 },
  { name: 'crime', description: 'Commit a crime for a chance at high rewards.', usage: '!!crime', category: 'Economy', aliases: [] },
  { name: 'slut', description: 'Take a risky job for money.', usage: '!!slut', category: 'Economy', aliases: [] },
  { name: 'rob', description: 'Steal coins from another user.', usage: '!!rob @user', category: 'Economy', aliases: ['steal'], popular: 2 },
  { name: 'give', description: 'Give your coins to someone else.', usage: '!!give @user [amount]', category: 'Economy', aliases: ['pay'] },
  { name: 'leaderboard', description: 'See the richest users in the server.', usage: '!!leaderboard', category: 'Economy', aliases: ['lb', 'rich'] },
  { name: 'blackjack', description: 'Play a game of blackjack for coins.', usage: '!!blackjack [bet]', category: 'Economy', aliases: ['bj'] },
  { name: 'coinflip', description: 'Flip a coin to double your bet.', usage: '!!coinflip [bet] [heads/tails]', category: 'Economy', aliases: ['cf'] },
  { name: 'roulette', description: 'Bet your money on roulette.', usage: '!!roulette [bet] [space]', category: 'Economy', aliases: [] },
  { name: 'stocks list', description: 'View available virtual stocks.', usage: '!!stocks list', category: 'Economy', aliases: [], popular: 3 },
  { name: 'stocks buy', description: 'Buy shares in a virtual stock.', usage: '!!stocks buy [symbol] [amount]', category: 'Economy', aliases: [], popular: 2 },
  { name: 'stocks sell', description: 'Sell your shares.', usage: '!!stocks sell [symbol] [amount]', category: 'Economy', aliases: [] },
  { name: 'portfolio', description: 'Check your current stock portfolio.', usage: '!!portfolio', category: 'Economy', aliases: [], popular: 1 },
  { name: 'stocks news', description: 'Check recent news affecting stock prices.', usage: '!!stocks news', category: 'Economy', aliases: [] },

  // Fun & Comedy
  { name: 'roast', description: 'Roast a user.', usage: '!!roast @user', category: 'Fun', aliases: [], popular: 3 },
  { name: 'confess', description: 'Send an anonymous confession.', usage: '!!confess [message]', category: 'Fun', aliases: [], popular: 3 },
  { name: 'match', description: 'Calculate the love match percentage.', usage: '!!match @user1 @user2', category: 'Fun', aliases: ['ship'] },
  { name: 'dm', description: 'Make the bot DM a user.', usage: '!!dm @user [message]', category: 'Fun', aliases: [], popular: 2 },

  // Utility
  { name: 'help', description: 'View the interactive help menu.', usage: '!!help', category: 'Utility', aliases: ['h'] },
  { name: 'botinfo', description: 'View statistics and info about SpaceX.', usage: '!!botinfo', category: 'Utility', aliases: ['bi', 'stats'] },
  { name: 'serverinfo', description: 'View info about the current server.', usage: '!!serverinfo', category: 'Utility', aliases: ['si'] },
  { name: 'avatar', description: 'Grab a user\'s avatar image.', usage: '!!avatar [@user]', category: 'Utility', aliases: ['av'] },
  { name: 'invite', description: 'Get the bot invite link.', usage: '!!invite', category: 'Utility', aliases: [] },
  { name: 'afk', description: 'Set your AFK status.', usage: '!!afk [reason]', category: 'Utility', aliases: [] },
  { name: 'remindme', description: 'Set a reminder.', usage: '!!remindme [time] [reminder]', category: 'Utility', aliases: ['remind'] },
  { name: 'rep', description: 'Give a reputation point to a user.', usage: '!!rep @user', category: 'Utility', aliases: [] },
];

// Helper to extract unique categories
export const getCategories = () => {
  const categories = commandData.map(cmd => cmd.category);
  return ['All', ...new Set(categories)];
};
