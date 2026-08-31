import { Search, X } from "lucide-react";
import { useEffect, useState } from "react";

import type { CollectorCity } from "../../api/client";
import { collectorApi } from "../../api/client";

type Props = {
  onClose: () => void;
  onCreated: () => void;
};

export function CollectorDialog({ onClose, onCreated }: Props) {
  const [keyword, setKeyword] = useState("运维实习生");
  const [city, setCity] = useState("上海");
  const [cities, setCities] = useState<CollectorCity[]>([]);
  const [limit, setLimit] = useState(20);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    collectorApi.cities().then((result) => {
      if (active) setCities(result.items);
    }).catch(() => {
      if (active) setError("读取BOSS地点目录失败, 请稍后重试.");
    });
    return () => { active = false; };
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await collectorApi.createTask({ source: "boss", keyword: keyword.trim(), city: city.trim(), limit });
      onCreated();
    } catch {
      setError("创建采集任务失败, 请检查本机伴侣状态.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal collector-dialog" role="dialog" aria-modal="true" aria-label="采集BOSS职位">
        <div className="modal-header">
          <div><p className="eyebrow">BOSS直聘</p><h2>采集职位</h2></div>
          <button className="icon-button" onClick={onClose} aria-label="关闭"><X size={18} /></button>
        </div>
        <form onSubmit={submit}>
          <label>搜索关键词
            <input value={keyword} onChange={(event) => setKeyword(event.target.value)} required autoFocus />
          </label>
          <div className="collector-form-row">
            <label>城市
              <input
                value={city}
                onChange={(event) => setCity(event.target.value)}
                list="boss-city-options"
                placeholder="输入城市名称"
                autoComplete="off"
                required
              />
              <datalist id="boss-city-options">
                {cities.map((item) => <option value={item.name} key={item.code} />)}
              </datalist>
            </label>
            <label>采集数量
              <input type="number" min={1} max={50} value={limit} onChange={(event) => setLimit(Number(event.target.value))} required />
            </label>
          </div>
          {error && <p className="form-error">{error}</p>}
          <div className="form-actions">
            <button type="button" className="secondary" onClick={onClose}>取消</button>
            <button type="submit" disabled={submitting || !keyword.trim() || !city.trim() || limit < 1 || limit > 50}>
              <Search size={16} />{submitting ? "正在创建" : "开始后台采集"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
