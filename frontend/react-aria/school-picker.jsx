import { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { I18nProvider } from 'react-aria/I18nProvider';
import { UNSAFE_PortalProvider } from 'react-aria/PortalProvider';
import {
  Autocomplete, Button, Dialog, Heading, Input, Label,
  ListBox, ListBoxItem, Modal, ModalOverlay, SearchField, Text,
} from 'react-aria-components';
import './school-picker.css';

function Icon({ name, ...props }) {
  const paths = {
    search: <><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></>,
    arrow: <><path d="M5 12h14m-6-6 6 6-6 6" /></>,
    close: <path d="m6 6 12 12M6 18 18 6" />,
  };
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>;
}

function SchoolPicker({ schools, selectedSchool, accountChoice, busy, isOpen, onChoose, onDismiss, normalize }) {
  const [query, setQuery] = useState('');
  const matching = schools.filter(school => normalize([
    school.school_name, school.short_name, school.english_name, ...(school.aliases || []),
  ].filter(Boolean).join(' ')).includes(normalize(query)));

  return (
    <ModalOverlay isOpen={isOpen} onOpenChange={open => { if (!open) onDismiss(); }}
      isDismissable={!busy} isKeyboardDismissDisabled={busy}
      onEnter={element => { window.UniWayMotion?.dialog?.(element); }}
      className="school-onboarding aria-school-overlay">
      <Modal className="onboarding-shell aria-school-modal">
        <Dialog className="aria-school-dialog" aria-labelledby="onboarding-title" aria-busy={busy}>
          <Button id="onboarding-close" className="icon-button school-picker-close"
            aria-label="關閉學校選擇" isDisabled={busy} onPress={onDismiss}>
            <Icon name="close" />
          </Button>
          <div className="onboarding-heading">
            <span className="platform-mark" aria-hidden="true">
              <img src="/static/assets/brand/uniway-mark.webp?v=20261004-logo-2" alt="" width="48" height="48" />
            </span>
            <div>
              <span className="eyebrow">UniWay</span>
              <Heading id="onboarding-title" slot="title" level={1}>你目前就讀哪一所台灣大學？</Heading>
              <p>點一下你的學校，我們就會顯示你真正能申請的學校、資格與申請時程。</p>
              <p id="onboarding-lock-note" hidden={!accountChoice}>
                <strong>請選你實際就讀的學校：</strong>學校會顯示在你的帳號與貼文上，選定後 3 天內不能更換。
              </p>
            </div>
          </div>
          <Autocomplete inputValue={query} onInputChange={setQuery} disableAutoFocusFirst>
            <SearchField className="school-search-field" autoFocus isDisabled={busy}>
              <Label>搜尋台灣的大學</Label>
              <div className="control-with-icon">
                <Icon name="search" />
                <Input id="school-search" autoComplete="off"
                  placeholder="輸入校名、簡稱或英文名稱" />
                <Button className="icon-button school-search-clear" aria-label="清除學校搜尋"
                  isDisabled={busy}><Icon name="close" /></Button>
              </div>
            </SearchField>
            <p className="school-picker-help">用方向鍵瀏覽學校，按 Enter 確認；也可以直接點選。</p>
            <ListBox id="school-options" className="school-options" aria-label="可選擇的大學"
              items={matching} selectionMode="none" onAction={key => onChoose(String(key))}
              disabledKeys={busy ? schools.map(school => school.school_name) : []}
              renderEmptyState={() => <p id="school-search-empty" className="school-search-empty">
                未找到這所學校；目前支援的學校請查看選單，其他台灣大學會依資料查核進度加入。
              </p>}>
              {school => (
                <ListBoxItem id={school.school_name} textValue={school.school_name}
                  aria-label={`${school.school_name}${school.school_name === selectedSchool ? '，目前選擇' : ''}`}
                  data-home-school={school.school_name}
                  className={`school-option${school.school_name === selectedSchool ? ' selected' : ''}`}
                  style={{ '--school-tint': school.badgeTint }}>
                  <span className="school-emblem" aria-hidden="true">{school.badgeText}</span>
                  <Text slot="label" className="school-option-name">{school.school_name}</Text>
                  <Text slot="description" className="school-option-status">
                    {school.partner_count ? `${school.partner_count} 間合作校` : '資料建置中'}
                  </Text>
                  <Icon name="arrow" className="school-option-go" />
                </ListBoxItem>
              )}
            </ListBox>
          </Autocomplete>
          <p className="school-picker-status" role="status">{busy ? '正在切換學校，請稍候…' : ''}</p>
          <small className="privacy-note">瀏覽公開資料不需要登入；收藏、進度與社群功能才需要帳號。</small>
        </Dialog>
      </Modal>
    </ModalOverlay>
  );
}

// The app owns catalogue, account and workspace state. This adapter owns only UI.
const host = document.getElementById('school-onboarding');
if (host) {
  host.replaceChildren();
  host.className = 'school-picker-host';
  host.removeAttribute('role');
  host.removeAttribute('aria-modal');
  host.removeAttribute('aria-labelledby');
  const mount = document.createElement('div');
  host.append(mount);
  const root = createRoot(mount);
  let session = 0;
  const model = { isOpen: false, schools: [], selectedSchool: '', accountChoice: false, busy: false };
  const render = () => root.render(
    <I18nProvider locale="zh-TW">
      <UNSAFE_PortalProvider getContainer={() => host}>
        <SchoolPicker key={session} {...model} />
      </UNSAFE_PortalProvider>
    </I18nProvider>
  );

  window.UniWaySchoolPicker = {
    get isOpen() { return model.isOpen; },
    update(options) {
      Object.assign(model, options);
      if (model.isOpen) render();
    },
    open(options) {
      Object.assign(model, options, { isOpen: true, busy: false });
      session++;
      host.hidden = false;
      render();
    },
    close() {
      model.isOpen = false;
      model.busy = false;
      render();
      host.hidden = true;
    },
    setBusy(busy) {
      model.busy = busy;
      if (model.isOpen) render();
    },
  };
}
