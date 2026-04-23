/**
 * Campus Buzz - 配置常量
 */

const CONFIG = {
    WORKFLOW_URL: '/api',      // 通过 Presentation Service 反向代理
    POLL_INTERVAL: 2000,       // 轮询间隔（毫秒）
    MAX_POLL_COUNT: 30,        // 最大轮询次数
    PAGE_SIZE: 5               // 每页显示记录数
};

// 全局状态
let allRecords = [];           // 缓存所有记录（用于分页）
let currentPage = 1;
let currentModalRecord = null; // 缓存当前弹窗显示的记录
