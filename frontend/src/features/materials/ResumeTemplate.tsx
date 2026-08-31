import {
  Brain,
  BriefcaseBusiness,
  GraduationCap,
  ImageUp,
  LayoutList,
  Lightbulb,
  Wrench,
} from "lucide-react";
import type { ChangeEvent, ElementType, FocusEvent } from "react";

import type { ResumeSection } from "../../api/client";
import type { ResumePersonalDetails } from "./resumeDocument";

type EditableTextProps = {
  as?: "h1" | "h2" | "p" | "li";
  value: string;
  label: string;
  className?: string;
  onChange: (value: string) => void;
};

function EditableText({ as = "p", value, label, className, onChange }: EditableTextProps) {
  const Tag = as as ElementType;
  return (
    <Tag
      key={value}
      role="textbox"
      aria-label={label}
      className={className}
      contentEditable="true"
      suppressContentEditableWarning
      onBlur={(event: FocusEvent<HTMLElement>) => onChange(event.currentTarget.textContent?.trim() ?? "")}
    >
      {value}
    </Tag>
  );
}

const sectionIcons = {
  education: GraduationCap,
  experience: BriefcaseBusiness,
  work: BriefcaseBusiness,
  project: Wrench,
  skills: Lightbulb,
  skill: Lightbulb,
  summary: Brain,
} as const;

type ResumeTemplateProps = {
  personal: ResumePersonalDetails;
  summary: string;
  sections: ResumeSection[];
  onPersonalChange: (personal: ResumePersonalDetails) => void;
  onSummaryChange: (summary: string) => void;
  onSectionsChange: (sections: ResumeSection[]) => void;
};

export function ResumeTemplate({
  personal,
  summary,
  sections,
  onPersonalChange,
  onSummaryChange,
  onSectionsChange,
}: ResumeTemplateProps) {
  const updatePersonalList = (
    key: "basicInfo" | "contacts" | "honors",
    index: number,
    value: string,
  ) => {
    onPersonalChange({
      ...personal,
      [key]: personal[key].map((item, itemIndex) => itemIndex === index ? value : item),
    });
  };

  const uploadAvatar = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !["image/png", "image/jpeg", "image/webp"].includes(file.type)) return;
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      if (typeof reader.result === "string") {
        onPersonalChange({ ...personal, avatarDataUrl: reader.result });
      }
    });
    reader.readAsDataURL(file);
  };

  return (
    <div className="resume-canvas" aria-label="A4简历预览">
      <article className="resume-sheet">
        <aside className="resume-template-sidebar">
          <div className="resume-avatar">
            {personal.avatarDataUrl
              ? <img src={personal.avatarDataUrl} alt="头像" />
              : <span aria-hidden="true">{personal.name.trim().slice(0, 1) || "照"}</span>}
          </div>
          <label className="resume-avatar-upload no-print">
            <ImageUp size={14} aria-hidden="true" />
            上传头像
            <input
              aria-label="上传头像"
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={uploadAvatar}
            />
          </label>
          <EditableText
            as="h1"
            value={personal.name}
            label="姓名"
            className="resume-person-name"
            onChange={(name) => onPersonalChange({ ...personal, name })}
          />
          <EditableText
            value={personal.headline}
            label="求职意向"
            className="resume-person-headline"
            onChange={(headline) => onPersonalChange({ ...personal, headline })}
          />
          {([
            ["基本信息", "basicInfo"],
            ["联系方式", "contacts"],
            ["个人荣誉", "honors"],
          ] as const).map(([title, key]) => (
            <section className="resume-sidebar-block" key={key}>
              <h2>{title}</h2>
              <ul>
                {personal[key].map((item, index) => (
                  <EditableText
                    as="li"
                    key={`${key}-${index}`}
                    value={item}
                    label={`${title}${index + 1}`}
                    onChange={(value) => updatePersonalList(key, index, value)}
                  />
                ))}
              </ul>
            </section>
          ))}
        </aside>
        <div className="resume-template-main">
          <section className="resume-template-section resume-summary-section">
            <h2><Brain size={17} aria-hidden="true" />自我评价</h2>
            <EditableText
              value={summary}
              label="简历简介"
              className="resume-template-summary"
              onChange={onSummaryChange}
            />
          </section>
          {sections.map((section, sectionIndex) => {
            const Icon = sectionIcons[section.kind.toLowerCase() as keyof typeof sectionIcons] ?? LayoutList;
            return (
              <section className="resume-template-section" key={`${section.kind}-${sectionIndex}`}>
                <div className="resume-template-section-title">
                  <Icon size={17} aria-hidden="true" />
                  <EditableText
                    as="h2"
                    value={section.title}
                    label={`第${sectionIndex + 1}个模块标题`}
                    onChange={(title) => onSectionsChange(sections.map((item, index) => (
                      index === sectionIndex ? { ...item, title } : item
                    )))}
                  />
                </div>
                {section.bullets.map((bullet, bulletIndex) => (
                  <article className="resume-template-item" key={bulletIndex}>
                    <EditableText
                      value={bullet.text}
                      label={`${section.title}第${bulletIndex + 1}条`}
                      onChange={(text) => onSectionsChange(sections.map((item, index) => (
                        index === sectionIndex
                          ? {
                              ...item,
                              bullets: item.bullets.map((entry, itemIndex) => (
                                itemIndex === bulletIndex ? { ...entry, text } : entry
                              )),
                            }
                          : item
                      )))}
                    />
                    <span className="resume-source-note no-print">来源已验证</span>
                  </article>
                ))}
              </section>
            );
          })}
        </div>
      </article>
    </div>
  );
}
