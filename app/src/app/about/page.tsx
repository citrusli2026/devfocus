export default function About() {
  return (
    <div className="max-w-2xl mx-auto py-8 space-y-8">
      <section>
        <h1 className="text-3xl font-bold mb-4">关于 DevPulse</h1>
        <p className="text-gray-300 leading-relaxed">
          DevPulse（开发者脉搏）自动收集开发者关注的信息，整理成日报、周报、月报和年报。
          让你不用到处刷，一站式掌握技术动态。
        </p>
      </section>

      <section>
        <h2 className="text-xl font-bold mb-3">📡 数据来源</h2>
        <ul className="space-y-3 text-gray-300">
          <li className="flex items-start gap-2">
            <span className="text-orange-400 mt-0.5">🔥</span>
            <div>
              <strong>Hacker News</strong> — 全球最活跃的技术社区，每日热门话题
            </div>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-400 mt-0.5">📦</span>
            <div>
              <strong>GitHub Trending</strong> — 每日热门开源项目，发现新工具和框架
            </div>
          </li>
        </ul>
      </section>

      <section>
        <h2 className="text-xl font-bold mb-3">🔄 更新频率</h2>
        <ul className="space-y-2 text-gray-300">
          <li>• <strong>日报</strong> — 每日自动更新</li>
          <li>• <strong>周报</strong> — 每周汇总</li>
          <li>• <strong>月报</strong> — 即将推出</li>
          <li>• <strong>年报</strong> — 即将推出</li>
        </ul>
      </section>

      <section>
        <h2 className="text-xl font-bold mb-3">🛠 技术栈</h2>
        <p className="text-gray-300">
          数据管线：Python · 前端：Next.js + Tailwind CSS · 部署：静态导出
        </p>
      </section>
    </div>
  );
}
