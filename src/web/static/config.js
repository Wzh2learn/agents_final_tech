/**
 * 前端应用配置
 * 集中管理所有可配置的参数，避免硬编码
 */
const APP_CONFIG = {
  // ==================== WebSocket 配置 ====================
  
  /**
   * WebSocket 服务器端口
   * 开发环境使用固定的5001端口，生产环境应从环境变量或服务器配置获取
   */
  WS_PORT: window.location.hostname === 'localhost' ? 5001 : parseInt(window.location.port || 80),
  
  /**
   * WebSocket 最大重连次数
   * 超过此次数后停止重连，提示用户刷新页面
   */
  WS_RECONNECT_MAX_ATTEMPTS: 5,
  
  /**
   * WebSocket 重连基础延迟（毫秒）
   * 使用指数退避策略：delay = BASE_DELAY * 2^(attempt-1)
   */
  WS_RECONNECT_BASE_DELAY: 2000,
  
  // ==================== API 配置 ====================
  
  /**
   * API 请求超时时间（毫秒）
   */
  API_TIMEOUT: 30000,
  
  /**
   * API 失败后的最大重试次数
   */
  API_RETRY_MAX: 3,
  
  /**
   * API 基础路径
   * 方便在不同环境中切换API端点
   */
  API_BASE_URL: window.location.origin,
  
  // ==================== UI 配置 ====================
  
  /**
   * Toast 提示显示时长（毫秒）
   */
  TOAST_DURATION: 3000,
  
  /**
   * 消息列表分页大小
   */
  MESSAGE_PAGE_SIZE: 50,
  
  /**
   * 自动保存间隔（毫秒）
   * 用于定期保存用户输入的草稿
   */
  AUTOSAVE_INTERVAL: 5000,
  
  /**
   * 文档列表分页大小
   */
  DOCUMENT_PAGE_SIZE: 10,
  
  /**
   * 文件上传最大大小（字节）
   * 默认 50MB
   */
  MAX_FILE_SIZE: 50 * 1024 * 1024,
  
  // ==================== 功能开关 ====================
  
  /**
   * 是否启用调试模式
   * 调试模式下会输出更多日志信息
   */
  DEBUG: window.location.hostname === 'localhost',
  
  /**
   * 是否启用WebSocket连接
   */
  ENABLE_WEBSOCKET: true,
  
  /**
   * 是否启用缓存
   */
  ENABLE_CACHE: true,
  
  // ==================== 角色配置 ====================
  
  /**
   * 角色映射表
   * 将角色代码映射到完整的角色key和显示信息
   */
  ROLES: {
    'a': {
      key: 'product_manager',
      name: '产品经理',
      emoji: '👔',
      description: '业务需求、用户体验'
    },
    'b': {
      key: 'tech_developer',
      name: '技术开发',
      emoji: '💻',
      description: '技术实现、系统架构'
    },
    'c': {
      key: 'sales_operations',
      name: '销售运营',
      emoji: '📈',
      description: '客户案例、市场反馈'
    },
    'd': {
      key: 'default_engineer',
      name: '默认工程师',
      emoji: '🔧',
      description: '通用技术支持'
    }
  },
  
  // ==================== 辅助方法 ====================
  
  /**
   * 获取WebSocket URL
   * @returns {string} WebSocket连接URL
   */
  getWebSocketUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    return `${protocol}//${host}:${this.WS_PORT}`;
  },
  
  /**
   * 获取完整的API URL
   * @param {string} path - API路径（如 '/api/chat/sessions'）
   * @returns {string} 完整的API URL
   */
  getApiUrl(path) {
    return `${this.API_BASE_URL}${path}`;
  },
  
  /**
   * 根据角色代码获取角色信息
   * @param {string} roleCode - 角色代码 ('a', 'b', 'c', 'd')
   * @returns {Object|null} 角色信息对象或null
   */
  getRole(roleCode) {
    return this.ROLES[roleCode] || null;
  },
  
  /**
   * 记录调试日志
   * 只在调试模式下输出
   * @param {...any} args - 日志参数
   */
  log(...args) {
    if (this.DEBUG) {
      console.log('[APP_CONFIG]', ...args);
    }
  }
};

// 冻结配置对象，防止意外修改
Object.freeze(APP_CONFIG);
Object.freeze(APP_CONFIG.ROLES);

// 导出配置（如果使用模块化）
if (typeof module !== 'undefined' && module.exports) {
  module.exports = APP_CONFIG;
}
