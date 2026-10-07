const express = require('express');
const { getHealth, getAIHealth } = require('../controllers/healthController');

const router = express.Router();

router.get('/', getHealth);
router.get('/ai', getAIHealth);

module.exports = router;
