// 모듈 레지스트리. 슬롯 이름 -> 모듈. main.js 가 이 표대로 mount 한다.
// 모듈을 추가하려면 여기에 한 줄 + app-shell.js 의 SLOT_NAMES 에 슬롯을 더한다.
// (topbar·settings 는 레이아웃 소속이라 main.js 가 따로 mount 한다.)
import * as map from './components/map/index.js';
import * as cards from './components/cards/index.js';
import * as chat from './components/chat/index.js';
import * as securitylog from './components/securitylog/index.js';
import * as rationale from './components/rationale/index.js';
import * as timeline from './components/timeline/index.js';

export const MODULES = { chat, timeline, map, cards, rationale, securitylog };
