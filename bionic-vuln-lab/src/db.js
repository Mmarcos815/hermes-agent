// In-memory database for bionic-vuln-lab
// No native sqlite3 needed — pure JavaScript simulation

const users = [
  { id: 1, username: 'admin', password: 'admin123', email: 'admin@bionic.lab', role: 'admin', balance: 10000 },
  { id: 2, username: 'user1', password: 'password1', email: 'user1@bionic.lab', role: 'user', balance: 1000 },
  { id: 3, username: 'user2', password: 'password2', email: 'user2@bionic.lab', role: 'user', balance: 500 },
  { id: 4, username: 'user3', password: 'password3', email: 'user3@bionic.lab', role: 'user', balance: 250 },
];

const products = [
  { id: 1, name: 'Bionic T-Shirt', price: 25 },
  { id: 2, name: 'Bionic Hoodie', price: 50 },
  { id: 3, name: 'Bionic Sticker Pack', price: 10 },
];

const orders = [];
const baskets = [];

module.exports = {
  users,
  products,
  orders,
  baskets,
  query: (sql) => {
    // Simulate SQL queries for injection testing
    if (sql.includes('SELECT * FROM users WHERE')) {
      return users;
    }
    return [];
  },
  findUserById: (id) => users.find(u => u.id === parseInt(id)),
  findUserByUsername: (username) => users.find(u => u.username === username),
  addOrder: (order) => orders.push(order),
  getBasket: (userId) => baskets.filter(b => b.userId === userId),
};
