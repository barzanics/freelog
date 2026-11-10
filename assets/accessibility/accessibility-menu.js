const accessibilityMenuStyles = `
    :root {
      --border_radius: 25px;
    }
    
    .brz-acs-hidden {
      display: none !important;
    }
    
    #brz-acs-accessibility-modal,
    #brz-acs-accessibility-modal * {
      transition: all 0.3s ease 0s;
      font-size: 16px;
      line-height: 1;
      letter-spacing: 0;
      text-align: center;
      user-select: none;
    }
    
    #brz-acs-accessibility-modal {
      position: fixed;
      top: 5vh;
      width: 80%;
      max-width: 500px;
      height: auto;
      max-height: 63vh;
      background: rgb(var(--rgb-tenth-lighter));
      z-index: 999999999;
      justify-content: center;
      border-radius: var(--border_radius);
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      overflow: clip;
      display: flex;
      flex-direction: column;
    }
    
    #brz-acs-accessibility-modal #brz-acs-closeBtn {
      position: absolute;
      width: 50px;
      height: 50px;
      border-radius: var(--border_radius);
      background: rgb(var(--rgb-first));
      color: rgb(var(--rgb-lightest));
      cursor: pointer;
      overflow: clip;
      border: none;
      outline: none;
      display: flex;
      justify-content: center;
      align-items: center;
      transform: translate(0,-4px);
    }
    
    #brz-acs-accessibility-modal.brz-acs-left {
      left: 0;
      right: auto;
      border-radius: 0 var(--border_radius) var(--border_radius) 0;
    }
    
    #brz-acs-accessibility-modal.brz-acs-right {
      right: 0;
      left: auto;
      border-radius: var(--border_radius) 0 0 var(--border_radius);
    }
    
    #brz-acs-accessibility-modal.brz-acs-top {
      top: 0;
      left: 24px;
      height: auto;
      max-height: 63vh;
      border-radius: 0 0 var(--border_radius) var(--border_radius);
    }
    
    #brz-acs-accessibility-modal.brz-acs-close #brz-acs-closeBtn {
      top: 0 !important; 
      left: 0 !important;
      bottom: 0 !important;
      right: 0 !important;
    }

    /* TOP POSITIONS */
    #brz-acs-accessibility-modal.brz-acs-top-right {
      top: 20px;
      right: 24px;
      left: auto;
      bottom: auto;
      border-radius: var(--border_radius);
    }
    
    #brz-acs-accessibility-modal.brz-acs-top-right #brz-acs-closeBtn {
      top: 15px;
      right: 15px;
      left: auto;
      bottom: auto;
    }
    
    #brz-acs-accessibility-modal.brz-acs-top-right #brz-acs-headerContent {
      margin: 10px 70px 10px 10px;
    }
    
    #brz-acs-accessibility-modal.brz-acs-top-left {
      top: 20px;
      left: 24px;
      right: auto;
      bottom: auto;
      border-radius: var(--border_radius);
    }
    
    #brz-acs-accessibility-modal.brz-acs-top-left #brz-acs-closeBtn {
      top: 15px;
      left: 15px;
      right: auto;
      bottom: auto;
    }
    
    #brz-acs-accessibility-modal.brz-acs-top-left #brz-acs-headerContent {
      margin: 10px 10px 10px 70px;
    }
    
    /* BOTTOM POSITIONS */
    #brz-acs-accessibility-modal.brz-acs-bottom-right {
      bottom: 175px;
      right: 24px;
      top: auto;
      left: auto;
      border-radius: var(--border_radius);
      flex-direction: column-reverse;
    }

    @media only screen and (min-width: 768px) {
      #brz-acs-accessibility-modal.brz-acs-bottom-right {
        bottom: 118px;
      }
    }
    
    #brz-acs-accessibility-modal.brz-acs-bottom-right #brz-acs-closeBtn {
      bottom: 5px;
      right: 5px;
      left: auto;
      top: auto;
    }
    
    #brz-acs-accessibility-modal.brz-acs-bottom-right #brz-acs-headerContent {
      margin: 10px 70px 10px 10px;
    }

    #brz-acs-accessibility-modal.brz-acs-bottom-right #brz-acs-acc-footer {
      top: 0px;
      bottom: auto;
    }
      
    #brz-acs-accessibility-modal.brz-acs-bottom-right #brz-acs-accessibility-tools {
      margin-top: 130px;
      margin-bottom: 0;
    }
    
    #brz-acs-accessibility-modal.brz-acs-bottom-left #brz-acs-acc-footer {
      top: 0px;
      bottom: auto;
    }

    #brz-acs-accessibility-modal.brz-acs-bottom-left #brz-acs-accessibility-tools {
      margin-top: 130px;
      margin-bottom: 0;
    }

    #brz-acs-accessibility-modal.brz-acs-bottom-left {
      bottom: 175px;
      left: 24px;
      top: auto;
      right: auto;
      border-radius: var(--border_radius);
      flex-direction: column-reverse;
    }
      
    @media only screen and (min-width: 768px) {
      #brz-acs-accessibility-modal.brz-acs-bottom-left {
        bottom: 118px;
      }
    }
    #brz-acs-accessibility-modal.brz-acs-bottom-left #brz-acs-closeBtn {
      bottom: 5px;
      left: 5px;
      right: auto;
      top: auto;
    }
    
    #brz-acs-accessibility-modal.brz-acs-bottom-left #brz-acs-headerContent {
      margin: 10px 10px 10px 70px;
    }
    
    /* LEFT POSITIONS */
    #brz-acs-accessibility-modal.brz-acs-left-top {
      top: 20px;
      left: 24px;
      right: auto;
      bottom: auto;
      border-radius: var(--border_radius);
    }
    
    #brz-acs-accessibility-modal.brz-acs-left-top #brz-acs-closeBtn {
      top: 15px;
      right: 15px;
      left: auto;
      bottom: auto;
    }
    
    #brz-acs-accessibility-modal.brz-acs-left-top #brz-acs-headerContent {
      margin: 10px 70px 10px 10px;
    }
    
    #brz-acs-accessibility-modal.brz-acs-left-bottom {
      bottom: 175px;
      left: 24px;
      top: auto;
      right: auto;
      border-radius: var(--border_radius);
    }
      
    @media only screen and (min-width: 768px) {
      #brz-acs-accessibility-modal.brz-acs-left-bottom {
        bottom: 118px;
      }
    }

    #brz-acs-accessibility-modal.brz-acs-left-bottom #brz-acs-closeBtn {
      top: 15px;
      right: 15px;
      left: auto;
      bottom: auto;
    }
    
    #brz-acs-accessibility-modal.brz-acs-left-bottom #brz-acs-headerContent {
      margin: 10px 70px 10px 10px;
    }
    
    /* RIGHT POSITIONS */
    #brz-acs-accessibility-modal.brz-acs-right-top {
      top: 20px;
      right: 24px;
      left: auto;
      bottom: auto;
      border-radius: var(--border_radius);
    }
    
    #brz-acs-accessibility-modal.brz-acs-right-top #brz-acs-closeBtn {
      top: 15px;
      left: 15px;
      right: auto;
      bottom: auto;
    }
    
    #brz-acs-accessibility-modal.brz-acs-right-top #brz-acs-headerContent {
      margin: 10px 10px 10px 70px;
    }
        
    #brz-acs-accessibility-modal.brz-acs-right-bottom {
      bottom: 175px;
      right: 24px;
      top: auto;
      left: auto;
      border-radius: var(--border_radius);
    }
      
    @media only screen and (min-width: 768px) {
      #brz-acs-accessibility-modal.brz-acs-right-bottom {
        bottom: 118px;
      }
    }

    #brz-acs-accessibility-modal.brz-acs-right-bottom #brz-acs-closeBtn {
      top: 15px;
      left: 15px;
      right: auto;
      bottom: auto;
    }
    
    #brz-acs-accessibility-modal.brz-acs-right-bottom #brz-acs-headerContent {
      margin: 10px 10px 10px 70px;
    }
    
    /* CENTER POSITIONS */
    #brz-acs-accessibility-modal.brz-acs-center-top {
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      right: auto;
      bottom: auto;
      border-radius: var(--border_radius);
    }
    
    #brz-acs-accessibility-modal.brz-acs-center-top #brz-acs-closeBtn {
      top: 15px;
      left: 15px;
      right: auto;
      bottom: auto;
    }
    
    
    #brz-acs-accessibility-modal.brz-acs-center-bottom {
      bottom: 175px;
      left: 50%;
      transform: translateX(-50%);
      top: auto;
      right: auto;
      border-radius: var(--border_radius);
    }
      
    @media only screen and (min-width: 768px) {
      #brz-acs-accessibility-modal.brz-acs-center-bottom {
        bottom: 118px;
      }
    }

    #brz-acs-accessibility-modal.brz-acs-center-bottom #brz-acs-closeBtn {
      top: 15px;
      left: 15px;
      right: auto;
      bottom: auto;
    }
    
    #brz-acs-accessibility-modal.brz-acs-center-left {
      top: 50%;
      left: 24px;
      transform: translateY(-50%);
      right: auto;
      bottom: auto;
      border-radius: var(--border_radius);
    }
    
    #brz-acs-accessibility-modal.brz-acs-center-left #brz-acs-closeBtn {
      top: 15px;
      right: 15px;
      left: auto;
      bottom: auto;
    }
    
    #brz-acs-accessibility-modal.brz-acs-center-right {
      top: 50%;
      right: 24px;
      transform: translateY(-50%);
      left: auto;
      bottom: auto;
      border-radius: var(--border_radius);
    }
    
    #brz-acs-accessibility-modal.brz-acs-center-right #brz-acs-closeBtn {
      top: 15px;
      left: 15px;
      right: auto;
      bottom: auto;
    }
    
    #brz-acs-accessibility-modal.brz-acs-close {
      width: 50px;
      height: 50px;
      border-radius: var(--border_radius);
      cursor: pointer;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      overflow: clip;
      margin: 5px;
      padding: 0;
    }
    
    #brz-acs-accessibility-modal.brz-acs-close .brz-acs-acc-item {
      opacity: 0;
    }
    
    #brz-acs-accessibility-modal.brz-acs-close #brz-acs-closeBtn {
      position: absolute;
      width: 50px;
      height: 50px;
      border: none;
      background: none;
      color: rgb(var(--rgb-lightest));
      background: rgb(var(--rgb-first));
      font-size: 20px;
      cursor: pointer;
      margin: 0;
      transform: translate(0,0);
    }
    
    #brz-acs-accessibility-modal #brz-acs-closeBtn svg,
    #brz-acs-accessibility-modal #brz-acs-closeBtn i {
      width: 20px;
      height: 20px;
    }
    
    #brz-acs-accessibility-modal.brz-acs-close #brz-acs-closeBtn svg,
    #brz-acs-accessibility-modal.brz-acs-close #brz-acs-closeBtn i {
      width: 40px;
      height: 40px;
    }
    
    #brz-acs-accessibility-modal.brz-acs-close:hover #brz-acs-closeBtn {
      filter: opacity(0.8);
    }
    
    #brz-acs-accessibility-modal #brz-acs-headerContent {
      position: relative;
      display: flex;
      justify-content: center;
      align-items: center;
      width: calc(100% - 80px);
      height: 50px;
      background: rgb(var(--rgb-first));
      color: rgb(var(--rgb-lightest));
      border-radius: var(--border_radius);
      margin: 10px 10px 10px 70px;
    }
    
    #brz-acs-accessibility-modal.brz-acs-left #brz-acs-headerContent {
      margin: 10px 70px 10px 10px;
    }
    
    #brz-acs-accessibility-modal.brz-acs-right #brz-acs-headerContent {
      margin: 10px 10px 10px 70px;
    }
    
    #brz-acs-accessibility-modal #brz-acs-headerContent p {
      font-size: 20px;
      font-weight: 600;
    }
    
    #brz-acs-accessibility-modal.brz-acs-close #brz-acs-headerContent {
      display: none;
    }
    
    #brz-acs-accessibility-tools {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      align-items: start;
      width: 100%;
      height: auto;
      transition: all 0.3s ease 2s;
      overflow-y: auto;
      margin-bottom: 130px;
    }
    
    .brz-acs-acc-item {
      min-width: 120px;
      width: 33%;
      max-width: 200px;
      height: auto;
      margin: 0;
      cursor: pointer;
    }

    @media only screen and (max-width: 476px) {
      .brz-acs-acc-item {
        width: 49%;
      }
    }
    
  .brz-acs-acc-item:hover .brz-acs-acc-child {
      border-color: rgb(var(--rgb-seventh-darker));
      box-shadow: 0 0 3px rgb(var(--rgb-seventh));
    }
    
    .brz-acs-acc-item:hover .brz-acs-acc-child.brz-acs-active {
      filter: opacity(0.8);
      border: 1px solid rgb(var(--rgb-ninth-lighter));
      color: rgb(var(--rgb-ninth-lighter));
    }

    .brz-acs-acc-child {
      position: relative;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      width: auto;
      height: auto;
      aspect-ratio: 1/1;
      margin: 10px;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      color: rgb(var(--rgb-first));
      background-color: rgb(var(--rgb-ninth-lighter));
      box-shadow: 0 2px 12px -1px rgba(var(--rgb-darkest), 0.08);
      padding: 20px 16px 16px;
      border-radius: 12px;
      gap: 12px;
      transition: 150ms;
    }
    
    .brz-acs-acc-child.brz-acs-active {
      background: rgb(var(--rgb-first));
      color: rgb(var(--rgb-ninth-lighter));
      box-shadow: none;
      border: 1px solid rgb(var(--rgb-first));
    }

    .brz-acs-acc-child.brz-acs-active .brz-acs-acc-child-title {
      color: rgb(var(--rgb-lightest));
    }
    .brz-acs-acc-child-title {
      line-height: 24px !important;
      color: rgb(var(--rgb-light-dark));
      font-weight: 500;
      font-size: 14px;
      margin: 0;
      text-align: center;
      display: -webkit-box;
      -webkit-line-clamp: 1;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    
    .brz-acs-acc-progress-parent {
      display: flex;
      justify-content: space-between;
      width: 100%;
      padding-bottom: 10px;
    }
    
    .brz-acs-acc-progress-child {
      min-width: 30%;
      width: 48%;
      max-width: 48%;
      height: 3px;
      margin: 0 1%;
      background: rgb(var(--rgb-first));
      border-radius: 5px;
    }
    
    .brz-acs-acc-child.brz-acs-active .brz-acs-acc-progress-child {
      background: rgb(var(--rgb-ninth-lighter));
      opacity: 0.5;
    }
    
    .brz-acs-acc-child.brz-acs-active .brz-acs-acc-progress-child.brz-acs-active {
      opacity: 1;
    }
    
    #brz-acs-accessibility-tools svg,
    #brz-acs-accessibility-tools i,
    #brz-acs-accessibility-tools img {
      width: 30px;
      height: 30px;
      margin-bottom: 10px;
    }
    
    #brz-acs-change-positions {
      display: flex;
      align-items: center;
      justify-content: space-evenly;
      width: 100%;
      margin: auto;
      background: rgb(var(--rgb-first));
    }
    
    #brz-acs-change-positions button {
      width: auto;
      height: 30px;
      border: none;
      background: rgb(var(--rgb-first));
      color: rgb(var(--rgb-ninth-lighter));
      cursor: pointer;
      display: flex;
      justify-content: center;
      align-items: center;
      aspect-ratio: 1/1;
      padding: 20px 26px;
      margin: 10px 0;
      border-radius: var(--border_radius);
    }
    
    #brz-acs-change-positions button i {
      scale: 1.3;
      color: rgb(var(--rgb-ninth-lighter));
    }
    
    #brz-acs-change-positions button:hover {
      background: rgb(var(--rgb-ninth-lighter));
    }
  
    #brz-acs-change-positions button:hover i {
      scale: 1.2;
      color: rgb(var(--rgb-first));
    }
    
    #brz-acs-change-positions button.brz-acs-active {
      background: rgb(var(--rgb-ninth-lighter));
    }
    
    #brz-acs-change-positions button.brz-acs-active i {
      color: rgb(var(--rgb-first));
    }
    
    #brz-acs-acc-footer {
      display: flex;
      flex-direction: column;
      width: 100%;
      position: absolute;
      bottom: 0;
      left: 0;
    }
    
    #brz-acs-reset-all {
      width: calc(100% - 20px);
      height: 50px;
      background: rgb(var(--rgb-first));
      color: rgb(var(--rgb-ninth-lighter));
      border-radius: var(--border_radius);
      cursor: pointer;
      display: flex;
      justify-content: center;
      align-items: center;
      margin: 10px;
    }
    
    #brz-acs-reset-all:hover {
      filter: opacity(0.8);
    }
    
    /*Accessibility Tools*/
    
    .brz-acs-invert {
      filter: invert(1);
    }
    
    .brz-acs-grayscale {
      filter: grayscale(1);
    }
    
    .brz-acs-low-saturation {
      filter: saturate(20%);
    }
    
    .brz-acs-high-saturation {
      filter: saturate(200%);
    }
    
    .brz-acs-underline-style-0 a {
      text-decoration: none;
      background: black !important;
      color: yellow !important;
      font-weight: bolder;
    }
    
    .brz-acs-underline-style-0 a:hover,
    .brz-acs-underline-style-2 a:hover,
    .brz-acs-underline-style-1 a:hover {
      text-decoration: underline !important;
    }
    
    .brz-acs-underline-style-1 a {
      text-decoration: none;
      background: #FFD740 !important;
      color: #005A9C !important;
      font-weight: bolder;
    }
    
    .brz-acs-underline-style-2 a {
      text-decoration: none;
      background: white !important;
      color: black !important;
      font-weight: bolder;
    }
    
    .brz-acs-contrast-style-0 {
      filter: contrast(0.5);
    }
    
    .brz-acs-contrast-style-1 {
      filter: contrast(1.5);
    }
    
    .brz-acs-contrast-style-2 {
      filter: contrast(2);
    }
    
    /*Apply Two or more filters*/
    
    .brz-acs-invert.brz-acs-grayscale {
      filter: invert(1) grayscale(1);
    }
    
    .brz-acs-invert.brz-acs-low-saturation {
      filter: invert(1) saturate(20%);
    }
    
    .brz-acs-invert.brz-acs-high-saturation {
      filter: invert(1) saturate(200%);
    }
    
    .brz-acs-invert.brz-acs-contrast-style-0 {
      filter: invert(1) contrast(0.5);
    }
    
    .brz-acs-invert.brz-acs-contrast-style-1 {
      filter: invert(1) contrast(1.5);
    }
    
    .brz-acs-invert.brz-acs-contrast-style-2 {
      filter: invert(1) contrast(2);
    }
    
    .brz-acs-grayscale.brz-acs-low-saturation {
      filter: grayscale(1) saturate(20%);
    }
    
    .brz-acs-grayscale.brz-acs-high-saturation {
      filter: grayscale(1) saturate(200%);
    }
    
    .brz-acs-grayscale.brz-acs-contrast-style-0 {
      filter: grayscale(1) contrast(0.5);
    }
    
    .brz-acs-grayscale.brz-acs-contrast-style-1 {
      filter: grayscale(1) contrast(1.5);
    }
    
    .brz-acs-grayscale.brz-acs-contrast-style-2 {
      filter: grayscale(1) contrast(2);
    }
    
    .brz-acs-low-saturation.brz-acs-high-saturation {
      filter: saturate(20%) saturate(200%);
    }
    
    .brz-acs-low-saturation.brz-acs-contrast-style-0 {
      filter: saturate(20%) contrast(0.5);
    }
    
    .brz-acs-low-saturation.brz-acs-contrast-style-1 {
      filter: saturate(20%) contrast(1.5);
    }
    
    .brz-acs-low-saturation.brz-acs-contrast-style-2 {
      filter: saturate(20%) contrast(2);
    }
    
    .brz-acs-high-saturation.brz-acs-contrast-style-0 {
      filter: saturate(200%) contrast(0.5);
    }
    
    .brz-acs-high-saturation.brz-acs-contrast-style-1 {
      filter: saturate(200%) contrast(1.5);
    }
    
    .brz-acs-high-saturation.brz-acs-contrast-style-2 {
      filter: saturate(200%) contrast(2);
    }
    
    .brz-acs-contrast-style-0.brz-acs-contrast-style-1 {
      filter: contrast(0.5) contrast(1.5);
    }
    
    .brz-acs-contrast-style-0.brz-acs-contrast-style-2 {
      filter: contrast(0.5) contrast(2);
    }
    
    .brz-acs-contrast-style-1.brz-acs-contrast-style-2 {
      filter: contrast(1.5) contrast(2);
    }
    
    .brz-acs-invert.brz-acs-grayscale.brz-acs-low-saturation {
      filter: invert(1) grayscale(1) saturate(20%);
    }
    
    .brz-acs-invert.brz-acs-grayscale.brz-acs-high-saturation {
      filter: invert(1) grayscale(1) saturate(200%);
    }
    
    .brz-acs-invert.brz-acs-grayscale.brz-acs-contrast-style-0 {
      filter: invert(1) grayscale(1) contrast(0.5);
    }
    
    .brz-acs-invert.brz-acs-grayscale.brz-acs-contrast-style-1 {
      filter: invert(1) grayscale(1) contrast(1.5);
    }
    
    .brz-acs-invert.brz-acs-grayscale.brz-acs-contrast-style-2 {
      filter: invert(1) grayscale(1) contrast(2);
    }
    
    .brz-acs-invert.brz-acs-low-saturation.brz-acs-high-saturation {
      filter: invert(1) saturate(20%) saturate(200%);
    }
    
    .brz-acs-invert.brz-acs-low-saturation.brz-acs-contrast-style-0 {
      filter: invert(1) saturate(20%) contrast(0.5);
    }
    
    .brz-acs-invert.brz-acs-low-saturation.brz-acs-contrast-style-1 {
      filter: invert(1) saturate(20%) contrast(1.5);
    }
    
    .brz-acs-invert.brz-acs-low-saturation.brz-acs-contrast-style-2 {
      filter: invert(1) saturate(20%) contrast(2);
    }
    
    .brz-acs-invert.brz-acs-high-saturation.brz-acs-contrast-style-0 {
      filter: invert(1) saturate(200%) contrast(0.5);
    }
    
    .brz-acs-invert.brz-acs-high-saturation.brz-acs-contrast-style-1 {
      filter: invert(1) saturate(200%) contrast(1.5);
    }
    
    .brz-acs-invert.brz-acs-high-saturation.brz-acs-contrast-style-2 {
      filter: invert(1) saturate(200%) contrast(2);
    }
    
    .brz-acs-invert.brz-acs-contrast-style-0.brz-acs-contrast-style-1 {
      filter: invert(1) contrast(0.5) contrast(1.5);
    }
    
    .brz-acs-invert.brz-acs-contrast-style-0.brz-acs-contrast-style-2 {
      filter: invert(1) contrast(0.5) contrast(2);
    }
    
    .brz-acs-invert.brz-acs-contrast-style-1.brz-acs-contrast-style-2 {
      filter: invert(1) contrast(1.5) contrast(2);
    }
    
    .brz-acs-grayscale.brz-acs-low-saturation.brz-acs-high-saturation {
      filter: grayscale(1) saturate(20%) saturate(200%);
    }
    
    .brz-acs-grayscale.brz-acs-low-saturation.brz-acs-contrast-style-0 {
      filter: grayscale(1) saturate(20%) contrast(0.5);
    }
    
    .brz-acs-grayscale.brz-acs-low-saturation.brz-acs-contrast-style-1 {
      filter: grayscale(1) saturate(20%) contrast(1.5);
    }
    
    .brz-acs-grayscale.brz-acs-low-saturation.brz-acs-contrast-style-2 {
      filter: grayscale(1) saturate(20%) contrast(2);
    }
    
    .brz-acs-grayscale.brz-acs-high-saturation.brz-acs-contrast-style-0 {
      filter: grayscale(1) saturate(200%) contrast(0.5);
    }
    
    .brz-acs-grayscale.brz-acs-high-saturation.brz-acs-contrast-style-1 {
      filter: grayscale(1) saturate(200%) contrast(1.5);
    }
    
    .brz-acs-grayscale.brz-acs-high-saturation.brz-acs-contrast-style-2 {
      filter: grayscale(1) saturate(200%) contrast(2);
    }
    
    .brz-acs-grayscale.brz-acs-contrast-style-0.brz-acs-contrast-style-1 {
      filter: grayscale(1) contrast(0.5) contrast(1.5);
    }
    
    .brz-acs-grayscale.brz-acs-contrast-style-0.brz-acs-contrast-style-2 {
      filter: grayscale(1) contrast(0.5) contrast(2);
    }
    
    .brz-acs-grayscale.brz-acs-contrast-style-1.brz-acs-contrast-style-2 {
      filter: grayscale(1) contrast(1.5) contrast(2);
    }
    
    .brz-acs-low-saturation.brz-acs-high-saturation.brz-acs-contrast-style-0 {
      filter: saturate(20%) saturate(200%) contrast(0.5);
    }
    
    .brz-acs-low-saturation.brz-acs-high-saturation.brz-acs-contrast-style-1 {
      filter: saturate(20%) saturate(200%) contrast(1.5);
    }
    
    .brz-acs-low-saturation.brz-acs-high-saturation.brz-acs-contrast-style-2 {
      filter: saturate(20%) saturate(200%) contrast(2);
    }
    
    .brz-acs-low-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-1 {
      filter: saturate(20%) contrast(0.5) contrast(1.5);
    }
    
    .brz-acs-low-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-2 {
      filter: saturate(20%) contrast(0.5) contrast(2);
    }
    
    .brz-acs-low-saturation.brz-acs-contrast-style-1.brz-acs-contrast-style-2 {
      filter: saturate(20%) contrast(1.5) contrast(2);
    }
    
    .brz-acs-high-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-1 {
      filter: saturate(200%) contrast(0.5) contrast(1.5);
    }
    
    .brz-acs-high-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-2 {
      filter: saturate(200%) contrast(0.5) contrast(2);
    }
    
    .brz-acs-high-saturation.brz-acs-contrast-style-1.brz-acs-contrast-style-2 {
      filter: saturate(200%) contrast(1.5) contrast(2);
    }
    
    .brz-acs-contrast-style-0.brz-acs-contrast-style-1.brz-acs-contrast-style-2 {
      filter: contrast(0.5) contrast(1.5) contrast(2);
    }
    
    .brz-acs-invert.brz-acs-grayscale.brz-acs-low-saturation.brz-acs-high-saturation {
      filter: invert(1) grayscale(1) saturate(20%) saturate(200%);
    }
    
    .brz-acs-invert.brz-acs-grayscale.brz-acs-low-saturation.brz-acs-contrast-style-0 {
      filter: invert(1) grayscale(1) saturate(20%) contrast(0.5);
    }
    
    .brz-acs-invert.brz-acs-grayscale.brz-acs-low-saturation.brz-acs-contrast-style-1 {
      filter: invert(1) grayscale(1) saturate(20%) contrast(1.5);
    }
    
    .brz-acs-invert.brz-acs-grayscale.brz-acs-low-saturation.brz-acs-contrast-style-2 {
      filter: invert(1) grayscale(1) saturate(20%) contrast(2);
    }
    
    .brz-acs-invert.brz-acs-grayscale.brz-acs-high-saturation.brz-acs-contrast-style-0 {
      filter: invert(1) grayscale(1) saturate(200%) contrast(0.5);
    }
    
    .brz-acs-invert.brz-acs-grayscale.brz-acs-high-saturation.brz-acs-contrast-style-1 {
      filter: invert(1) grayscale(1) saturate(200%) contrast(1.5);
    }
    
    .brz-acs-invert.brz-acs-grayscale.brz-acs-high-saturation.brz-acs-contrast-style-2 {
      filter: invert(1) grayscale(1) saturate(200%) contrast(2);
    }
    
    .brz-acs-invert.brz-acs-low-saturation.brz-acs-high-saturation.brz-acs-contrast-style-0 {
      filter: invert(1) saturate(20%) saturate(200%) contrast(0.5);
    }
    
    .brz-acs-invert.brz-acs-low-saturation.brz-acs-high-saturation.brz-acs-contrast-style-1 {
      filter: invert(1) saturate(20%) saturate(200%) contrast(1.5);
    }
    
    .brz-acs-invert.brz-acs-low-saturation.brz-acs-high-saturation.brz-acs-contrast-style-2 {
      filter: invert(1) saturate(20%) saturate(200%) contrast(2);
    }
    
    .brz-acs-invert.brz-acs-low-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-1 {
      filter: invert(1) saturate(20%) contrast(0.5) contrast(1.5);
    }
    
    .brz-acs-invert.brz-acs-low-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-2 {
      filter: invert(1) saturate(20%) contrast(0.5) contrast(2);
    }
    
    .brz-acs-invert.brz-acs-low-saturation.brz-acs-contrast-style-1.brz-acs-contrast-style-2 {
      filter: invert(1) saturate(20%) contrast(1.5) contrast(2);
    }
    
    .brz-acs-invert.brz-acs-high-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-1 {
      filter: invert(1) saturate(200%) contrast(0.5) contrast(1.5);
    }
    
    .brz-acs-invert.brz-acs-high-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-2 {
      filter: invert(1) saturate(200%) contrast(0.5) contrast(2);
    }
    
    .brz-acs-invert.brz-acs-high-saturation.brz-acs-contrast-style-1.brz-acs-contrast-style-2 {
      filter: invert(1) saturate(200%) contrast(1.5) contrast(2);
    }
    
    .brz-acs-grayscale.brz-acs-low-saturation.brz-acs-high-saturation.brz-acs-contrast-style-0 {
      filter: grayscale(1) saturate(20%) saturate(200%) contrast(0.5);
    }
    
    .brz-acs-grayscale.brz-acs-low-saturation.brz-acs-high-saturation.brz-acs-contrast-style-1 {
      filter: grayscale(1) saturate(20%) saturate(200%) contrast(1.5);
    }
    
    .brz-acs-grayscale.brz-acs-low-saturation.brz-acs-high-saturation.brz-acs-contrast-style-2 {
      filter: grayscale(1) saturate(20%) saturate(200%) contrast(2);
    }
    
    .brz-acs-grayscale.brz-acs-low-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-1 {
      filter: grayscale(1) saturate(20%) contrast(0.5) contrast(1.5);
    }
    
    .brz-acs-grayscale.brz-acs-low-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-2 {
      filter: grayscale(1) saturate(20%) contrast(0.5) contrast(2);
    }
    
    .brz-acs-grayscale.brz-acs-low-saturation.brz-acs-contrast-style-1.brz-acs-contrast-style-2 {
      filter: grayscale(1) saturate(20%) contrast(1.5) contrast(2);
    }
    
    .brz-acs-grayscale.brz-acs-high-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-1 {
      filter: grayscale(1) saturate(200%) contrast(0.5) contrast(1.5);
    }
    
    .brz-acs-grayscale.brz-acs-high-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-2 {
      filter: grayscale(1) saturate(200%) contrast(0.5) contrast(2);
    }
    
    .brz-acs-grayscale.brz-acs-high-saturation.brz-acs-contrast-style-1.brz-acs-contrast-style-2 {
      filter: grayscale(1) saturate(200%) contrast(1.5) contrast(2);
    }
    
    .brz-acs-low-saturation.brz-acs-high-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-1 {
      filter: saturate(20%) saturate(200%) contrast(0.5) contrast(1.5);
    }
    
    .brz-acs-low-saturation.brz-acs-high-saturation.brz-acs-contrast-style-0.brz-acs-contrast-style-2 {
      filter: saturate(20%) saturate(200%) contrast(0.5) contrast(2);
    }
    
    .brz-acs-low-saturation.brz-acs-high-saturation.brz-acs-contrast-style-1.brz-acs-contrast-style-2 {
      filter: saturate(20%) saturate(200%) contrast(1.5) contrast(2);
    }
    
    .brz-acs-hide-images img {
      display: none;
    }
    
    .brz-acs-hide-video video {
      display: none;
    }
    
    .brz-acs-line-height-0 * {
      line-height: 1.5;
    }
    
    .brz-acs-line-height-1 * {
      line-height: 1.8;
    }
    
    .brz-acs-line-height-2 * {
      line-height: 2;
    }
    
    #brz-acs-cursor {
      position: fixed;
      z-index: 999999999;
      pointer-events: none;
      top: 0;
      left: 0;
    }
    
    #brz-acs-cursor.brz-acs-cursor-0 {
      width: 50px;
      height: auto;
      aspect-ratio: 1/1;
      background: rgba(255, 0, 0, 0.5);
      border: 2px solid rgb(var(--rgb-ninth-lighter));
      box-shadow: 0 0 20px 0 rgb(var(--rgb-ninth-lighter));
      border-radius: 50%;
      mix-blend-mode: difference;
      transition: all 0.1s ease;
      transform-origin: center;
      transform: translate(-50%, -50%);
    }
    
    #brz-acs-cursor.brz-acs-cursor-1 {
      width: 100%;
      height: 15vh;
      background: transparent;
      border: 10px solid rgb(var(--rgb-ninth-lighter));
      border-left: 0;
      border-right: 0;
      box-shadow: 0 0 0 100vh rgb(0 0 0 / 50%);
      transition: none;
      transform: translate(0, -50%);
    }
    
    #brz-acs-cursor.brz-acs-cursor-2 {
      width: 25vw;
      height: 8px;
      background: rgb(var(--rgb-first));
      border: yellow 2px solid;
      transition: all 0.1s ease;
      transform-origin: center;
      transform: translate(-50%, 50%);
    }
    
    #brz-acs-triangle-cursor {
      width: 0;
      height: 0;
      border-left: 10px solid transparent;
      border-right: 10px solid transparent;
      border-bottom: 10px solid yellow;
      position: fixed;
      top: 0;
      left: 0;
      transform: translate(-50%, -50%);
      transition: all 0.1s ease;
      z-index: 999999998;
      pointer-events: none;
      display: none;
    }
    /* Draggable floating styles */
    #brz-acs-accessibility-modal.brz-acs-floating {
        width: 50px !important;
        height: 50px !important;
        max-width: 50px !important;
        max-height: 50px !important;
        border-radius: 25px !important;
        background: transparent !important;
        box-shadow: none !important;
        cursor: move;
    }

    #brz-acs-accessibility-modal.brz-acs-floating #brz-acs-accessibility-tools,
    #brz-acs-accessibility-modal.brz-acs-floating #brz-acs-headerContent,
    #brz-acs-accessibility-modal.brz-acs-floating #brz-acs-acc-footer {
        display: none !important;
    }

    #brz-acs-accessibility-modal.brz-acs-floating #brz-acs-closeBtn {
        position: static !important;
        width: 50px !important;
        height: 50px !important;
        margin: 0 !important;
        transform: none !important;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.2) !important;
        cursor: move !important;
    }

    /* Position classes for floating modal */
    #brz-acs-accessibility-modal.brz-acs-top #brz-acs-closeBtn {
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2) !important;
    }

    #brz-acs-accessibility-modal.brz-acs-bottom #brz-acs-closeBtn {
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.2) !important;
    }

    /* Dragging state */
    #brz-acs-accessibility-modal.brz-acs-dragging {
        transition: none !important;
        opacity: 0.8;
    }

    #brz-acs-accessibility-modal.brz-acs-dragging #brz-acs-closeBtn {
        cursor: grabbing !important;
    }
`;

const accessibilityMenuHTML = `
    <div id="brz-acs-accessibility-modal" class="brz-acs-close" style="z-index: 999999999;">
      <button id="brz-acs-closeBtn" style="z-index: 999999999;">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-universal-access-circle" viewBox="0 0 16 16">
          <path d="M8 4.143A1.071 1.071 0 1 0 8 2a1.071 1.071 0 0 0 0 2.143m-4.668 1.47 3.24.316v2.5l-.323 4.585A.383.383 0 0 0 7 13.14l.826-4.017c.045-.18.301-.18.346 0L9 13.139a.383.383 0 0 0 .752-.125L9.43 8.43v-2.5l3.239-.316a.38.38 0 0 0-.047-.756H3.379a.38.38 0 0 0-.047.756Z" />
          <path d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0M1 8a7 7 0 1 1 14 0A7 7 0 0 1 1 8" />
        </svg>
      </button>
      <div id="brz-acs-headerContent">
        <p class="mb-0 py-4 text-lightest">ابزار دسترسی آسان</p>
      </div>
      <div id="brz-acs-accessibility-tools" class="standard-scrollbar">
    
        <!--invert colors-->
        <div class="brz-acs-acc-item">
          <div class="brz-acs-acc-child" id="brz-acs-invert-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-droplet-half" viewBox="0 0 16 16">
              <path fill-rule="evenodd" d="M7.21.8C7.69.295 8 0 8 0q.164.544.371 1.038c.812 1.946 2.073 3.35 3.197 4.6C12.878 7.096 14 8.345 14 10a6 6 0 0 1-12 0C2 6.668 5.58 2.517 7.21.8m.413 1.021A31 31 0 0 0 5.794 3.99c-.726.95-1.436 2.008-1.96 3.07C3.304 8.133 3 9.138 3 10c0 0 2.5 1.5 5 .5s5-.5 5-.5c0-1.201-.796-2.157-2.181-3.7l-.03-.032C9.75 5.11 8.5 3.72 7.623 1.82z" />
              <path fill-rule="evenodd" d="M4.553 7.776c.82-1.641 1.717-2.753 2.093-3.13l.708.708c-.29.29-1.128 1.311-1.907 2.87z" />
            </svg>
            <p class="brz-acs-acc-child-title">معکوس کردن رنگ‌ها</p>
            <div class="brz-acs-acc-progress-parent brz-acs-hidden">
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-1"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-2"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-3"></div>
            </div>
          </div>
        </div>
    
        <!--grayscale-->
        <div class="brz-acs-acc-item">
          <div class="brz-acs-acc-child" id="brz-acs-grayscale">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="black" class="bi bi-circle-half" viewBox="0 0 16 16">
              <path d="M8 15A7 7 0 1 0 8 1zm0 1A8 8 0 1 1 8 0a8 8 0 0 1 0 16" />
            </svg>
            <p class="brz-acs-acc-child-title">مقیاس خاکستری</p>
            <div class="brz-acs-acc-progress-parent brz-acs-hidden">
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-1"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-2"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-3"></div>
            </div>
          </div>
        </div>
    
        <!--saturation-->
        <div class="brz-acs-acc-item">
          <div class="brz-acs-acc-child" id="brz-acs-saturation">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-palette" viewBox="0 0 16 16">
              <path d="M8 5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3m4 3a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3M5.5 7a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m.5 6a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3" />
              <path d="M16 8c0 3.15-1.866 2.585-3.567 2.07C11.42 9.763 10.465 9.473 10 10c-.603.683-.475 1.819-.351 2.92C9.826 14.495 9.996 16 8 16a8 8 0 1 1 8-8m-8 7c.611 0 .654-.171.655-.176.078-.146.124-.464.07-1.119-.014-.168-.037-.37-.061-.591-.052-.464-.112-1.005-.118-1.462-.10-.707.083-1.61.704-2.314.369-.417.845-.578 1.272-.618.404-.038.812.026 1.16.104.343.077.702.186 1.025.284l.028.008c.346.105.658.199.953.266.653.148.904.083.991.024C14.717 9.38 15 9.161 15 8a7 7 0 1 0-7 7" />
            </svg>
            <p class="brz-acs-acc-child-title">شدت رنگ پایین</p>
            <div class="brz-acs-acc-progress-parent brz-acs-hidden">
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-1"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-2"></div>
            </div>
          </div>
        </div>
    
        <!--links highlight-->
        <div class="brz-acs-acc-item">
          <div class="brz-acs-acc-child" id="brz-acs-underline">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-link-45deg" viewBox="0 0 16 16">
              <path d="M4.715 6.542 3.343 7.914a3 3 0 1 0 4.243 4.243l1.828-1.829A3 3 0 0 0 8.586 5.5L8 6.086a1 1 0 0 0-.154.199 2 2 0 0 1 .861 3.337L6.88 11.45a2 2 0 1 1-2.83-2.83l.793-.792a4 4 0 0 1-.128-1.287z" />
              <path d="M6.586 4.672A3 3 0 0 0 7.414 9.5l.775-.776a2 2 0 0 1-.896-3.346L9.12 3.55a2 2 0 1 1 2.83 2.83l-.793.792c.112.42.155.855.128 1.287l1.372-1.372a3 3 0 1 0-4.243-4.243z" />
            </svg>
            <p class="brz-acs-acc-child-title">برجسته‌سازی لینک‌ها</p>
            <div class="brz-acs-acc-progress-parent brz-acs-hidden">
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-1"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-2"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-3"></div>
            </div>
          </div>
        </div>
    
        <!--font size-->
        <div class="brz-acs-acc-item">
          <div class="brz-acs-acc-child" id="brz-acs-font-size">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M17 12V17H17.5C17.7761 17 18 17.2239 18 17.5C18 17.7761 17.7761 18 17.5 18H15.5C15.2239 18 15 17.7761 15 17.5C15 17.2239 15.2239 17 15.5 17H16V12H14V12.5C14 12.7761 13.7761 13 13.5 13C13.2239 13 13 12.7761 13 12.5V11.5C13 11.2239 13.2239 11 13.5 11H19.5C19.7761 11 20 11.2239 20 11.5V12.5C20 12.7761 19.7761 13 19.5 13C19.2239 13 19 12.7761 19 12.5V12H17ZM10 6V17H11.5C11.7761 17 12 17.2239 12 17.5C12 17.7761 11.7761 18 11.5 18H7.5C7.22386 18 7 17.7761 7 17.5C7 17.2239 7.22386 17 7.5 17H9V6H5V7.5C5 7.77614 4.77614 8 4.5 8C4.22386 8 4 7.77614 4 7.5V5.5C4 5.22386 4.22386 5 4.5 5H14.5C14.7761 5 15 5.22386 15 5.5V7.5C15 7.77614 14.7761 8 14.5 8C14.2239 8 14 7.77614 14 7.5V6H10Z" fill="black" />
            </svg>
            <p class="brz-acs-acc-child-title">اندازه قلم</p>
            <div class="brz-acs-acc-progress-parent brz-acs-hidden">
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-1"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-2"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-3"></div>
            </div>
          </div>
        </div>
    
        <!--line height-->
        <div class="brz-acs-acc-item">
          <div class="brz-acs-acc-child" id="brz-acs-line-height">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M19 5.70711V17.2929L20.1464 16.1464C20.3417 15.9512 20.6583 15.9512 20.8536 16.1464C21.0488 16.3417 21.0488 16.6583 20.8536 16.8536L18.8536 18.8536C18.6583 19.0488 18.3417 19.0488 18.1464 18.8536L16.1464 16.8536C15.9512 16.6583 15.9512 16.3417 16.1464 16.1464C16.3417 15.9512 16.6583 15.9512 16.8536 16.1464L18 17.2929V5.70711L16.8536 6.85355C16.6583 7.04882 16.3417 7.04882 16.1464 6.85355C15.9512 6.65829 15.9512 6.34171 16.1464 6.14645L18.1464 4.14645C18.3417 3.95118 18.6583 3.95118 18.8536 4.14645L20.8536 6.14645C21.0488 6.34171 21.0488 6.65829 20.8536 6.85355C20.6583 7.04882 20.3417 7.04882 20.1464 6.85355L19 5.70711ZM8 18V5H4V6.5C4 6.77614 3.77614 7 3.5 7C3.22386 7 3 6.77614 3 6.5V4.5C3 4.22386 3.22386 4 3.5 4H13.5C13.7761 4 14 4.22386 14 4.5V6.5C14 6.77614 13.7761 7 13.5 7C13.2239 7 13 6.77614 13 6.5V5H9V18H10.5C10.7761 18 11 18.2239 11 18.5C11 18.7761 10.7761 19 10.5 19H6.5C6.22386 19 6 18.7761 6 18.5C6 18.2239 6.22386 18 6.5 18H8Z" fill="black" />
            </svg>
            <p class="brz-acs-acc-child-title">فاصله خطوط</p>
            <div class="brz-acs-acc-progress-parent brz-acs-hidden">
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-1"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-2"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-3"></div>
            </div>
          </div>
        </div>
    
        <!--letter spacing-->
        <div class="brz-acs-acc-item">
          <div class="brz-acs-acc-child" id="brz-acs-letter-spacing">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M13 13H14.5C14.7761 13 15 13.2239 15 13.5C15 13.7761 14.7761 14 14.5 14H10.5C10.2239 14 10 13.7761 10 13.5C10 13.2239 10.2239 13 10.5 13H12V5H5V6.5C5 6.77614 4.77614 7 4.5 7C4.22386 7 4 6.77614 4 6.5V4.5C4 4.22386 4.22386 4 4.5 4H20.5C20.7761 4 21 4.22386 21 4.5V6.5C21 6.77614 20.7761 7 20.5 7C20.2239 7 20 6.77614 20 6.5V5H13V13ZM5.70711 18H19.2929L18.1464 16.8536C17.9512 16.6583 17.9512 16.3417 18.1464 16.1464C18.3417 15.9512 18.6583 15.9512 18.8536 16.1464L20.8536 18.1464C21.0488 18.3417 21.0488 18.6583 20.8536 18.8536L18.8536 20.8536C18.6583 21.0488 18.3417 21.0488 18.1464 20.8536C17.9512 20.6583 17.9512 20.3417 18.1464 20.1464L19.2929 19H5.70711L6.85355 20.1464C7.04882 20.3417 7.04882 20.6583 6.85355 20.8536C6.65829 21.0488 6.34171 21.0488 6.14645 20.8536L4.14645 18.8536C3.95118 18.6583 3.95118 18.3417 4.14645 18.1464L6.14645 16.1464C6.34171 15.9512 6.65829 15.9512 6.85355 16.1464C7.04882 16.3417 7.04882 16.6583 6.85355 16.8536L5.70711 18Z" fill="black" />
            </svg>
            <p class="brz-acs-acc-child-title">فاصله حروف</p>
            <div class="brz-acs-acc-progress-parent brz-acs-hidden">
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-1"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-2"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-3"></div>
            </div>
          </div>
        </div>
    
        <!--text align-->
        <div class="brz-acs-acc-item">
          <div class="brz-acs-acc-child" id="brz-acs-text-align">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M4.5 7C4.22386 7 4 6.77614 4 6.5C4 6.22386 4.22386 6 4.5 6H19.5C19.7761 6 20 6.22386 20 6.5C20 6.77614 19.7761 7 19.5 7H4.5ZM4.5 15C4.22386 15 4 14.7761 4 14.5C4 14.2239 4.22386 14 4.5 14H19.5C19.7761 14 20 14.2239 20 14.5C20 14.7761 19.7761 15 19.5 15H4.5ZM4.5 11C4.22386 11 4 10.7761 4 10.5C4 10.2239 4.22386 10 4.5 10H13.5C13.7761 10 14 10.2239 14 10.5C14 10.7761 13.7761 11 13.5 11H4.5ZM4.5 19C4.22386 19 4 18.7761 4 18.5C4 18.2239 4.22386 18 4.5 18H13.5C13.7761 18 14 18.2239 14 18.5C14 18.7761 13.7761 19 13.5 19H4.5Z" fill="black"/>
            </svg>
            <p class="brz-acs-acc-child-title">تراز متن</p>
            <div class="brz-acs-acc-progress-parent brz-acs-hidden">
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-1"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-2"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-3"></div>
            </div>
          </div>
        </div>
    
        <!--contrast-->
        <div class="brz-acs-acc-item">
          <div class="brz-acs-acc-child" id="brz-acs-contrast">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-transparency" viewBox="0 0 16 16">
              <path d="M0 6.5a6.5 6.5 0 0 1 12.346-2.846 a6.5 6.5 0 1 1-8.691 8.691A6.5 6.5 0 0 1 0 6.5m5.144 6.358a5.5 5.5 0 1 0 7.714-7.714 a6.5 6.5 0 0 1-7.714 7.714m-.733-1.269q.546.226 1.144.33l-1.474-1.474q.104.597.33 1.144m2.614.386a5.5 5.5 0 0 0 1.173-.242L4.374 7.91a6 6 0 0 0-.296 1.118zm2.157-.672q.446-.25.838-.576L5.418 6.126a6 6 0 0 0-.587.826zm1.545-1.284q.325-.39.576-.837L6.953 4.83a6 6 0 0 0-.827.587l4.6 4.602Zm1.006-1.822q.183-.562.242-1.172L9.028 4.078q-.58.096-1.118.296l3.823 3.824Zm.186-2.642a5.5 5.5 0 0 0-.33-1.144 a5.5 5.5 0 0 0-1.144-.33z" />
            </svg>
            <p class="brz-acs-acc-child-title">کنتراست</p>
            <div class="brz-acs-acc-progress-parent brz-acs-hidden">
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-1"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-2"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-3"></div>
            </div>
          </div>
        </div>
    
        <!--hide images-->
        <div class="brz-acs-acc-item">
          <div class="brz-acs-acc-child" id="brz-acs-hide-images">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="black" xmlns="http://www.w3.org/2000/svg">
              <path d="M4.8,4L4.8,4l1,1L4.8,4z M19.7,19L19.7,19l0.8,0.8L19.7,19z" />
              <path d="M18,7h-2c-0.5,0-1,0.5-1,1v2c0,0.5,0.5,1,1,1h2c0.5,0,1-0.5,1-1V8C19,7.5,18.5,7,18,7z M18,10h-2V8h2V10z" />
              <path d="M22,6.5v11c0,0.6-0.2,1.1-0.6,1.6l-0.6-0.6l-0.1-0.1l-4.9-4.9l0.3-0.3c0.2-0.2,0.5-0.2,0.7,0l4.2,4.1V6.5\tC21,5.7,20.3,5,19.5,5H7.4l-1-1h13.1C20.9,4,22,5.1,22,6.5z" />
              <path d="M1.9,1.1L1.1,1.9l2.4,2.4C2.6,4.6,2,5.5,2,6.5v11C2,18.9,3.1,20,4.5,20h14.8l2.9,2.9l0.7-0.7L1.9,1.1z M3,6.5\tC3,5.8,3.5,5.1,4.3,5l10,10l-0.8,0.8l-5.7-5.6c-0.2-0.2-0.5-0.2-0.7,0L3,14.3V6.5z M4.5,19C3.7,19,3,18.3,3,17.5v-1.8l4.5-4.5\tl5.7,5.6c0.2,0.2,0.5,0.2,0.7,0l1.1-1.1l3.3,3.3H4.5z" />
            </svg>
            <p class="brz-acs-acc-child-title">پنهان کردن تصویر</p>
          </div>
        </div>
    
        <!--hide video-->
        <div class="brz-acs-acc-item">
          <div class="brz-acs-acc-child" id="brz-acs-hide-video">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-camera-video-off" viewBox="0 0 16 16">
              <path fill-rule="evenodd" d="M10.961 12.365a2 2 0 0 0 .522-1.103l3.11 1.382A1 1 0 0 0 16 11.731V4.269a1 1 0 0 0-1.406-.913l-3.111 1.382A2 2 0 0 0 9.5 3H4.272l.714 1H9.5a1 1 0 0 1 1 1v6a1 1 0 0 1-.144.518zM1.428 4.18A1 1 0 0 0 1 5v6a1 1 0 0 0 1 1h5.014l.714 1H2a2 2 0 0 1-2-2V5c0-.675.334-1.272.847-1.634zM15 11.73l-3.5-1.555v-4.35L15 4.269zm-4.407 3.56-10-14 .814-.58 10 14z" />
            </svg>
            <p class="brz-acs-acc-child-title">پنهان کردن ویدیو</p>
          </div>
        </div>
    
        <!--change cursor-->
        <div class="brz-acs-acc-item">
          <div class="brz-acs-acc-child" id="brz-acs-change-cursor">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8.85333 19.8536C8.58758 20.1193 8.13463 20.0079 8.02253 19.6492L3.02253 3.64915C2.90221 3.26413 3.26389 2.90246 3.64891 3.02278L19.6489 8.02278C20.0076 8.13487 20.1191 8.58782 19.8533 8.85357L16.2069 12.5L20.8533 17.1465C21.0486 17.3417 21.0486 17.6583 20.8533 17.8536L17.8533 20.8536C17.6581 21.0488 17.3415 21.0488 17.1462 20.8536L12.4998 16.2071L8.85333 19.8536ZM4.26173 4.26197L8.73053 18.5621L12.1462 15.1465C12.3415 14.9512 12.6581 14.9512 12.8533 15.1465L17.4998 19.7929L19.7927 17.5L15.1462 12.8536C14.951 12.6583 14.951 12.3417 15.1462 12.1465L18.5619 8.73078L4.26173 4.26197Z" fill="black" />
            </svg>
            <p class="brz-acs-acc-child-title">تغییر نشانگر</p>
            <div class="brz-acs-acc-progress-parent brz-acs-hidden">
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-1"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-2"></div>
              <div class="brz-acs-acc-progress-child brz-acs-acc-progress-child-3"></div>
            </div>
          </div>
        </div>
      </div>
    
      <!--cursor and triangle cursor-->
      <div id="brz-acs-cursor"></div>
      <div id="brz-acs-triangle-cursor"></div>
    
      <!--accessibility modal footer-->
      <div id="brz-acs-acc-footer">
    
        <!--reset all-->
        <button id="brz-acs-reset-all">
          بازنشانی همه
        </button>
    
        <!--change positions-->
        <div id="brz-acs-change-positions">
          <button id="brz-acs-align-acc-bottom-right"><i class="fa-regular fa-objects-align-bottom fa-rtl"></i></button>
          <button id="brz-acs-align-acc-top-left"><i class="fa-regular fa-objects-align-top"></i></button>
          <button id="brz-acs-align-acc-bottom-left"><i class="fa-regular fa-objects-align-bottom"></i></button>
          <button id="brz-acs-align-acc-top-right"><i class="fa-regular fa-objects-align-right"></i></button>
        </div>
      </div>
    </div>
`;

$(document).ready(function() {
  // State variables
  let saturationClickCount = 0;
  let underlineClickCount = 0;
  let fontSizeClickCount = 0;
  let lineHeightClickCount = 0;
  let letterSpacingClickCount = 0;
  let textAlignClickCount = 0;
  let contrastClickCount = 0;
  let cursorClickCount = 0;
  let isRTLMode = false;

  // Initialize accessibility menu
  const accessibilityMenuStyleElement = $('<style>').html(accessibilityMenuStyles);
  $('head').append(accessibilityMenuStyleElement);
  $('body').append(accessibilityMenuHTML);

  // Get essential elements
  const docElement = $('html');
  let accessibilityModal, cursor;

  $(document).on("click", ".brz-acs-acc-item", function() {
      const $item = $(this);
      const $accChild = $item.find('.brz-acs-acc-child');
      $accChild.toggleClass('brz-acs-active');
      
      $item.find('path').each(function() {
          $(this).css('fill', $accChild.hasClass('brz-acs-active') ? 'rgb(var(--rgb-ninth-lighter))' : 'rgb(var(--rgb-first))');
      });
  });

  $(document).on("click", "#brz-acs-invert-colors", function() {
      docElement.toggleClass('brz-acs-invert');
  });

  $(document).on("click", "#brz-acs-grayscale", function() {
      docElement.toggleClass('brz-acs-grayscale');
  });

  $(document).on("click", "#brz-acs-saturation", function() {
      handleSaturationClick();
  });

  $(document).on("click", "#brz-acs-underline", function() {
      handleUnderlineClick();
  });

  $(document).on("click", "#brz-acs-font-size", function() {
      handleFontSizeClick();
  });

  $(document).on("click", "#brz-acs-line-height", function() {
      handleLineHeightClick();
  });

  $(document).on("click", "#brz-acs-letter-spacing", function() {
      handleLetterSpacingClick();
  });

  $(document).on("click", "#brz-acs-text-align", function() {
      handleTextAlignClick();
  });

  $(document).on("click", "#brz-acs-contrast", function() {
      handleContrastClick();
  });

  $(document).on("click", "#brz-acs-hide-images", function() {
      docElement.toggleClass('brz-acs-hide-images');
  });

  $(document).on("click", "#brz-acs-hide-video", function() {
      docElement.toggleClass('brz-acs-hide-video');
  });

  $(document).on("click", "#brz-acs-change-cursor", function() {
      handleCursorClick();
  });

  $(document).on("click", "#brz-acs-reset-all", function() {
      resetAllSettings();
  });

  // Cursor movement events
  $(document).on('mousemove', function(e) {
      cursor = $('#brz-acs-cursor');
      if (!cursor.length) return;
      
      if (cursor.hasClass('brz-acs-cursor-0')) {
          cursor.css({
              top: e.clientY + 'px',
              left: e.clientX + 'px'
          });
      } else if (cursor.hasClass('brz-acs-cursor-1')) {
          cursor.css({
              top: e.clientY + 'px',
              left: '0'
          });
      } else if (cursor.hasClass('brz-acs-cursor-2')) {
          let leftPos = e.clientX;
          if (e.clientX < window.innerWidth / 8) {
              leftPos = window.innerWidth / 8;
          } else if (e.clientX > window.innerWidth - window.innerWidth / 8) {
              leftPos = window.innerWidth - window.innerWidth / 8;
          }
          cursor.css({
              top: e.clientY + 'px',
              left: leftPos + 'px'
          });
          
          const triangle = $('#brz-acs-triangle-cursor');
          if (triangle.length) {
              triangle.css({
                  top: e.clientY + 'px',
                  left: e.clientX + 'px'
              });
          }
      }
  });

  // Hover effects for links and buttons
  $(document).on('mouseenter', 'a, button', function() {
      cursor = $('#brz-acs-cursor');
      if (cursor.length && cursor.hasClass('brz-acs-cursor-0')) {
          cursor.css({
              width: '100px',
              height: '100px'
          });
      }
  });

  $(document).on('mouseleave', 'a, button', function() {
      cursor = $('#brz-acs-cursor');
      if (cursor.length && cursor.hasClass('brz-acs-cursor-0')) {
          cursor.css({
              width: '50px',
              height: '50px'
          });
      }
  });

  // Core functions
  function accessibilityModalOpenCloseToggle() {
    accessibilityModal = $('#brz-acs-accessibility-modal');
    const closeBtn = $('#brz-acs-closeBtn');
    if (!accessibilityModal.length || !closeBtn.length) return;
    
    accessibilityModal.toggleClass('brz-acs-close');
    closeBtn.html(accessibilityModal.hasClass('brz-acs-close') ? 
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-universal-access-circle" viewBox="0 0 16 16"><path d="M8 4.143A1.071 1.071 0 1 0 8 2a1.071 1.071 0 0 0 0 2.143m-4.668 1.47 3.24.316v2.5l-.323 4.585A.383.383 0 0 0 7 13.14l.826-4.017c.045-.18.301-.18.346 0L9 13.139a.383.383 0 0 0 .752-.125L9.43 8.43v-2.5l3.239-.316a.38.38 0 0 0-.047-.756H3.379a.38.38 0 0 0-.047.756Z"></path><path d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0M1 8a7 7 0 1 1 14 0A7 7 0 0 1 1 8"></path></svg>' :
        accessibilityModal.hasClass('brz-acs-bottom-left') ? '<i class="fa-regular fa-chevron-up"></i>' :
        accessibilityModal.hasClass('brz-acs-bottom-right') ? '<i class="fa-regular fa-chevron-up"></i>' :
        accessibilityModal.hasClass('brz-acs-top-left') ? '<i class="fa-regular fa-chevron-down"></i>' :
        accessibilityModal.hasClass('brz-acs-top-right') ? '<i class="fa-regular fa-chevron-down"></i>' : '<i class="fa-regular fa-chevron-up"></i>');
    saveCurrentPosition();
    updateFloatingPositionClass();
  }

  const allPositions = [
    'brz-acs-top-left', 'brz-acs-top-right', 'brz-acs-bottom-left', 'brz-acs-bottom-right',
    'brz-acs-left-top', 'brz-acs-left-bottom', 'brz-acs-right-top', 'brz-acs-right-bottom',
    'brz-acs-center-top', 'brz-acs-center-bottom', 'brz-acs-center-left', 'brz-acs-center-right'
  ];
  function handlePositionChange(positionClass) {
    const modal = $('#brz-acs-accessibility-modal');
    // Remove all position classes
    modal.removeClass(allPositions.join(' ') + ' brz-acs-floating brz-acs-dragging');
    modal.css({
      top: '',
      left: '',
      right: '',
      bottom: '',
      transform: '',
      inset: '',
      zIndex: '999999999',
    });
    // Add new position class
    modal.addClass(positionClass);
    
    // If modal is closed, add close class
    if (!modal.hasClass('brz-acs-close')) {
      accessibilityModalOpenCloseToggle();
    }
    
    saveCurrentPosition();
    positionActiveStatus();
  }

  function positionActiveStatus() {
    const modal = $('#brz-acs-accessibility-modal');
    const currentPosition = allPositions.find(pos => modal.hasClass(pos)) || '';
    
    // Update position buttons active state
    $('[id^="brz-acs-align-"]').removeClass('brz-acs-active');
    
    if (currentPosition) {
        const buttonId = currentPosition.replace('brz-acs-', 'acc-');
        $(`#brz-acs-align-${buttonId}`).addClass('brz-acs-active');
    }
  }

  // Handler functions for accessibility features
  function handleSaturationClick() {
      const item = $('#brz-acs-saturation');
      if (!item.length) return;

      if (saturationClickCount === 2) {
          saturationClickCount = 0;
          item.find('p').text('شدت رنگ پایین');
          item.find('.brz-acs-acc-progress-parent').addClass('brz-acs-hidden');
          item.addClass('brz-acs-active');
          docElement.removeClass('brz-acs-high-saturation brz-acs-low-saturation');
      } else {
          item.removeClass('brz-acs-active');
          item.find('p').text('شدت رنگ');
          if (saturationClickCount === 0) {
              docElement.addClass('brz-acs-low-saturation');
              item.find('p').text('شدت رنگ پایین');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
          } else if (saturationClickCount === 1) {
              docElement.removeClass('brz-acs-low-saturation').addClass('brz-acs-high-saturation');
              item.find('p').text('شدت رنگ بالا');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
          }
          saturationClickCount++;
      }
  }

  function handleUnderlineClick() {
      const item = $('#brz-acs-underline');
      if (!item.length) return;

      if (underlineClickCount === 3) {
          underlineClickCount = 0;
          item.find('.brz-acs-acc-progress-parent').addClass('brz-acs-hidden');
          item.addClass('brz-acs-active');
          docElement.removeClass('brz-acs-underline brz-acs-underline-style-0 brz-acs-underline-style-1 brz-acs-underline-style-2');
      } else {
          item.removeClass('brz-acs-active');
          if (underlineClickCount === 0) {
              docElement.addClass('brz-acs-underline');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
              docElement.addClass('brz-acs-underline-style-0').removeClass('brz-acs-underline-style-1 brz-acs-underline-style-2');
          } else if (underlineClickCount === 1) {
              docElement.removeClass('brz-acs-underline-style-0').addClass('brz-acs-underline-style-1').removeClass('brz-acs-underline-style-2');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (underlineClickCount === 2) {
              docElement.removeClass('brz-acs-underline-style-0 brz-acs-underline-style-1').addClass('brz-acs-underline-style-2');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
          }
          underlineClickCount++;
      }
  }

  function handleFontSizeClick() {
      const item = $('#brz-acs-font-size');
      if (!item.length) return;

      if (fontSizeClickCount === 3) {
          fontSizeClickCount = 0;
          item.find('.brz-acs-acc-progress-parent').addClass('brz-acs-hidden');
          item.addClass('brz-acs-active');
          docElement.css('fontSize', '');
      } else {
          item.removeClass('brz-acs-active');
          if (fontSizeClickCount === 0) {
              docElement.css('fontSize', '1.3rem');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (fontSizeClickCount === 1) {
              docElement.css('fontSize', '1.5rem');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (fontSizeClickCount === 2) {
              docElement.css('fontSize', '1.8rem');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
          }
          fontSizeClickCount++;
      }
  }

  function handleLineHeightClick() {
      const item = $('#brz-acs-line-height');
      if (!item.length) return;

      if (lineHeightClickCount === 3) {
          lineHeightClickCount = 0;
          item.find('.brz-acs-acc-progress-parent').addClass('brz-acs-hidden');
          item.addClass('brz-acs-active');
          docElement.removeClass('brz-acs-line-height-0 brz-acs-line-height-1 brz-acs-line-height-2');
      } else {
          item.removeClass('brz-acs-active');
          if (lineHeightClickCount === 0) {
              docElement.addClass('brz-acs-line-height-0').removeClass('brz-acs-line-height-1 brz-acs-line-height-2');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (lineHeightClickCount === 1) {
              docElement.removeClass('brz-acs-line-height-0').addClass('brz-acs-line-height-1').removeClass('brz-acs-line-height-2');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (lineHeightClickCount === 2) {
              docElement.removeClass('brz-acs-line-height-0 brz-acs-line-height-1').addClass('brz-acs-line-height-2');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
          }
          lineHeightClickCount++;
      }
  }

  function handleLetterSpacingClick() {
      const item = $('#brz-acs-letter-spacing');
      if (!item.length) return;

      if (letterSpacingClickCount === 3) {
          letterSpacingClickCount = 0;
          item.find('.brz-acs-acc-progress-parent').addClass('brz-acs-hidden');
          item.addClass('brz-acs-active');
          docElement.css('letterSpacing', '');
      } else {
          item.removeClass('brz-acs-active');
          if (letterSpacingClickCount === 0) {
              docElement.css('letterSpacing', '0.1rem');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (letterSpacingClickCount === 1) {
              docElement.css('letterSpacing', '0.2rem');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (letterSpacingClickCount === 2) {
              docElement.css('letterSpacing', '0.3rem');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
          }
          letterSpacingClickCount++;
      }
  }

  function handleTextAlignClick() {
      const item = $('#brz-acs-text-align');
      if (!item.length) return;

      if (textAlignClickCount === 3) {
          textAlignClickCount = 0;
          item.find('.brz-acs-acc-progress-parent').addClass('brz-acs-hidden');
          item.addClass('brz-acs-active');
          docElement.css('textAlign', '');
      } else {
          item.removeClass('brz-acs-active');
          if (textAlignClickCount === 0) {
              docElement.css('textAlign', 'left');
              item.parent().find('svg').html(`<path d="M4.5 7C4.22386 7 4 6.77614 4 6.5C4 6.22386 4.22386 6 4.5 6H19.5C19.7761 6 20 6.22386 20 6.5C20 6.77614 19.7761 7 19.5 7H4.5ZM4.5 15C4.22386 15 4 14.7761 4 14.5C4 14.2239 4.22386 14 4.5 14H19.5C19.7761 14 20 14.2239 20 14.5C20 14.7761 19.7761 15 19.5 15H4.5ZM4.5 11C4.22386 11 4 10.7761 4 10.5C4 10.2239 4.22386 10 4.5 10H13.5C13.7761 10 14 10.2239 14 10.5C14 10.7761 13.7761 11 13.5 11H4.5ZM4.5 19C4.22386 19 4 18.7761 4 18.5C4 18.2239 4.22386 18 4.5 18H13.5C13.7761 18 14 18.2239 14 18.5C14 18.7761 13.7761 19 13.5 19H4.5Z" fill="black"/>`);
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (textAlignClickCount === 1) {
              docElement.css('textAlign', 'center');
              item.parent().find('svg').html(`<path d="M4.5 7C4.22386 7 4 6.77614 4 6.5C4 6.22386 4.22386 6 4.5 6H19.5C19.7761 6 20 6.22386 20 6.5C20 6.77614 19.7761 7 19.5 7H4.5ZM4.5 15C4.22386 15 4 14.7761 4 14.5C4 14.2239 4.22386 14 4.5 14H19.5C19.7761 14 20 14.2239 20 14.5C20 14.7761 19.7761 15 19.5 15H4.5ZM7.5 11C7.22386 11 7 10.7761 7 10.5C7 10.2239 7.22386 10 7.5 10H16.5C16.7761 10 17 10.2239 17 10.5C17 10.7761 16.7761 11 16.5 11H7.5ZM7.5 19C7.22386 19 7 18.7761 7 18.5C7 18.2239 7.22386 18 7.5 18H16.5C16.7761 18 17 18.2239 17 18.5C17 18.7761 16.7761 19 16.5 19H7.5Z" fill="black"/>`);
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (textAlignClickCount === 2) {
              docElement.css('textAlign', 'right');
              item.parent().find(`svg`).html(`<path d="M4.5 7C4.22386 7 4 6.77614 4 6.5C4 6.22386 4.22386 6 4.5 6H19.5C19.7761 6 20 6.22386 20 6.5C20 6.77614 19.7761 7 19.5 7H4.5ZM4.5 15C4.22386 15 4 14.7761 4 14.5C4 14.2239 4.22386 14 4.5 14H19.5C19.7761 14 20 14.2239 20 14.5C20 14.7761 19.7761 15 19.5 15H4.5ZM10.5 11C10.2239 11 10 10.7761 10 10.5C10 10.2239 10.2239 10 10.5 10H19.5C19.7761 10 20 10.2239 20 10.5C20 10.7761 19.7761 11 19.5 11H10.5ZM10.5 19C10.2239 19 10 18.7761 10 18.5C10 18.2239 10.2239 18 10.5 18H19.5C19.7761 18 20 18.2239 20 18.5C20 18.7761 19.7761 19 19.5 19H10.5Z" fill="black"/>`);
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
          }
          textAlignClickCount++;
      }
  }

  function handleContrastClick() {
      const item = $('#brz-acs-contrast');
      if (!item.length) return;

      if (contrastClickCount === 3) {
          contrastClickCount = 0;
          item.find('.brz-acs-acc-progress-parent').addClass('brz-acs-hidden');
          item.addClass('brz-acs-active');
          docElement.removeClass('brz-acs-contrast brz-acs-contrast-style-0 brz-acs-contrast-style-1 brz-acs-contrast-style-2');
      } else {
          item.removeClass('brz-acs-active');
          if (contrastClickCount === 0) {
              docElement.addClass('brz-acs-contrast');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
              docElement.addClass('brz-acs-contrast-style-0').removeClass('brz-acs-contrast-style-1 brz-acs-contrast-style-2');
          } else if (contrastClickCount === 1) {
              docElement.removeClass('brz-acs-contrast-style-0').addClass('brz-acs-contrast-style-1').removeClass('brz-acs-contrast-style-2');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (contrastClickCount === 2) {
              docElement.removeClass('brz-acs-contrast-style-0 brz-acs-contrast-style-1').addClass('brz-acs-contrast-style-2');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
          }
          contrastClickCount++;
      }
  }

  function handleCursorClick() {
      const item = $('#brz-acs-change-cursor');
      cursor = $('#brz-acs-cursor');
      const triangle = $('#brz-acs-triangle-cursor');
      if (!item.length || !cursor.length) return;

      if (triangle.length) {
          triangle.css('display', 'none');
      }

      if (cursorClickCount === 3) {
          cursorClickCount = 0;
          item.find('.brz-acs-acc-progress-parent').addClass('brz-acs-hidden');
          item.addClass('brz-acs-active');
          cursor.removeClass('brz-acs-cursor-0 brz-acs-cursor-1 brz-acs-cursor-2');
          docElement.css('cursor', '');
      } else {
          item.removeClass('brz-acs-active');
          if (cursorClickCount === 0) {
              cursor.addClass('brz-acs-cursor-0').removeClass('brz-acs-cursor-1 brz-acs-cursor-2');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
              cursor.css({ width: '50px', height: '50px' });
          } else if (cursorClickCount === 1) {
              cursor.removeClass('brz-acs-cursor-0').addClass('brz-acs-cursor-1').removeClass('brz-acs-cursor-2');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
              cursor.css({ width: '100%', height: '15vh' });
          } else if (cursorClickCount === 2) {
              cursor.removeClass('brz-acs-cursor-0 brz-acs-cursor-1').addClass('brz-acs-cursor-2');
              docElement.css('cursor', 'none');
              item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
              if (triangle.length) triangle.css('display', 'block');
              cursor.css({ width: '25vw', height: '8px' });
          }
          cursorClickCount++;
      }
  }

  function resetAllSettings() {
      cursor = $('#brz-acs-cursor');
      const triangle = $('#brz-acs-triangle-cursor');

      // Reset all the accessibility settings
      docElement.removeClass('brz-acs-invert brz-acs-grayscale brz-acs-high-saturation brz-acs-low-saturation brz-acs-underline-style-0 brz-acs-underline-style-1 brz-acs-underline-style-2 brz-acs-line-height-0 brz-acs-line-height-1 brz-acs-line-height-2 brz-acs-contrast brz-acs-contrast-style-0 brz-acs-contrast-style-1 brz-acs-contrast-style-2 brz-acs-hide-images brz-acs-hide-video')
               .css({
                   fontSize: '',
                   letterSpacing: '',
                   textAlign: '',
                   cursor: ''
               });

      if (cursor.length) {
          cursor.removeClass('brz-acs-cursor-0 brz-acs-cursor-1 brz-acs-cursor-2').css({ width: '', height: '' });
      }

      // Reset the cursor
      if (triangle.length) {
          triangle.css('display', 'none');
      }

      // Reset the progress bar
      $('.brz-acs-acc-progress-parent').addClass('brz-acs-hidden');

      // Reset the active state of the accessibility tools
      $('.brz-acs-acc-child').removeClass('brz-acs-active').find('path').css('fill', 'rgb(var(--rgb-first))');

      // Reset all counts to 0
      saturationClickCount = underlineClickCount = fontSizeClickCount = lineHeightClickCount = 
      letterSpacingClickCount = textAlignClickCount = contrastClickCount = cursorClickCount = 0;
  }

  // Save/load settings functions
  function saveSettings() {
      accessibilityModal = $('#brz-acs-accessibility-modal');
      cursor = $('#brz-acs-cursor');
      if (!cursor.length) return;
      
      const settings = {
          invertColors: docElement.hasClass('brz-acs-invert'),
          grayscale: docElement.hasClass('brz-acs-grayscale'),
          highSaturation: docElement.hasClass('brz-acs-high-saturation'),
          lowSaturation: docElement.hasClass('brz-acs-low-saturation'),
          underlineStyle0: docElement.hasClass('brz-acs-underline-style-0'),
          underlineStyle1: docElement.hasClass('brz-acs-underline-style-1'),
          underlineStyle2: docElement.hasClass('brz-acs-underline-style-2'),
          fontSize: docElement.css('fontSize'),
          lineHeight0: docElement.hasClass('brz-acs-line-height-0'),
          lineHeight1: docElement.hasClass('brz-acs-line-height-1'),
          lineHeight2: docElement.hasClass('brz-acs-line-height-2'),
          letterSpacing: docElement.css('letterSpacing'),
          textAlign: docElement.css('textAlign'),
          contrast: docElement.hasClass('brz-acs-contrast'),
          contrastStyle0: docElement.hasClass('brz-acs-contrast-style-0'),
          contrastStyle1: docElement.hasClass('brz-acs-contrast-style-1'),
          contrastStyle2: docElement.hasClass('brz-acs-contrast-style-2'),
          hideImages: docElement.hasClass('brz-acs-hide-images'),
          hideVideo: docElement.hasClass('brz-acs-hide-video'),
          cursor0: cursor.hasClass('brz-acs-cursor-0'),
          cursor1: cursor.hasClass('brz-acs-cursor-1'),
          cursor2: cursor.hasClass('brz-acs-cursor-2'),
          accPosition: accessibilityModal.hasClass('brz-acs-top-left') ? 'brz-acs-top-left' : 
                      accessibilityModal.hasClass('brz-acs-top-right') ? 'brz-acs-top-right' : 
                      accessibilityModal.hasClass('brz-acs-bottom-left') ? 'brz-acs-bottom-left' : 
                      accessibilityModal.hasClass('brz-acs-bottom-right') ? 'brz-acs-bottom-right' : 'brz-acs-bottom-left'
      };
      localStorage.setItem('brz-acs-accessibility-settings', JSON.stringify(settings));
      // Also save floating position
      saveCurrentPosition();
  }

  // Load saved settings when page loads
  function loadSavedSettings() {
      const savedSettings = JSON.parse(localStorage.getItem('brz-acs-accessibility-settings'));
      accessibilityModal = $('#brz-acs-accessibility-modal');
      cursor = $('#brz-acs-cursor');
      
      if (!savedSettings || !cursor.length) return;

      // Apply all saved settings
      if (savedSettings.invertColors) docElement.addClass('brz-acs-invert');
      if (savedSettings.grayscale) docElement.addClass('brz-acs-grayscale');
      if (savedSettings.highSaturation) docElement.addClass('brz-acs-high-saturation');
      if (savedSettings.lowSaturation) docElement.addClass('brz-acs-low-saturation');
      if (savedSettings.underlineStyle0) docElement.addClass('brz-acs-underline-style-0');
      if (savedSettings.underlineStyle1) docElement.addClass('brz-acs-underline-style-1');
      if (savedSettings.underlineStyle2) docElement.addClass('brz-acs-underline-style-2');
      if (savedSettings.fontSize) docElement.css('fontSize', savedSettings.fontSize);
      if (savedSettings.lineHeight0) docElement.addClass('brz-acs-line-height-0');
      if (savedSettings.lineHeight1) docElement.addClass('brz-acs-line-height-1');
      if (savedSettings.lineHeight2) docElement.addClass('brz-acs-line-height-2');
      if (savedSettings.letterSpacing) docElement.css('letterSpacing', savedSettings.letterSpacing);
      if (savedSettings.textAlign) docElement.css('textAlign', savedSettings.textAlign);
      if (savedSettings.contrast) docElement.addClass('brz-acs-contrast');
      if (savedSettings.contrastStyle0) docElement.addClass('brz-acs-contrast-style-0');
      if (savedSettings.contrastStyle1) docElement.addClass('brz-acs-contrast-style-1');
      if (savedSettings.contrastStyle2) docElement.addClass('brz-acs-contrast-style-2');
      if (savedSettings.hideImages) docElement.addClass('brz-acs-hide-images');
      if (savedSettings.hideVideo) docElement.addClass('brz-acs-hide-video');
      if (savedSettings.cursor0) cursor.addClass('brz-acs-cursor-0');
      if (savedSettings.cursor1) cursor.addClass('brz-acs-cursor-1');
      if (savedSettings.cursor2) cursor.addClass('brz-acs-cursor-2');

      // Set modal position
      if (accessibilityModal.length && savedSettings.accPosition) {
          accessibilityModal.removeClass(allPositions.join(' ') + ' brz-acs-floating brz-acs-dragging').addClass(savedSettings.accPosition);
      }

      // Load floating position
      loadSavedPosition();

      positionActiveStatus();
      setActiveStatus();
  }

  // Set active status
  function setActiveStatus() {
      cursor = $('#brz-acs-cursor');
      if (!cursor.length) return;

      // Set active status based on current state
      $('#brz-acs-invert-colors').toggleClass('brz-acs-active', docElement.hasClass('brz-acs-invert'));
      $('#brz-acs-grayscale').toggleClass('brz-acs-active', docElement.hasClass('brz-acs-grayscale'));
      $('#brz-acs-hide-images').toggleClass('brz-acs-active', docElement.hasClass('brz-acs-hide-images'));
      $('#brz-acs-hide-video').toggleClass('brz-acs-active', docElement.hasClass('brz-acs-hide-video'));

      // Saturation
      if (docElement.hasClass('brz-acs-high-saturation') || docElement.hasClass('brz-acs-low-saturation')) {
          const item = $('#brz-acs-saturation');
          item.addClass('brz-acs-active');
          item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
          if (docElement.hasClass('brz-acs-high-saturation')) {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
          } else if (docElement.hasClass('brz-acs-low-saturation')) {
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
          }
      }

      // Underline
      if (docElement.hasClass('brz-acs-underline-style-0') || docElement.hasClass('brz-acs-underline-style-1') || docElement.hasClass('brz-acs-underline-style-2')) {
          const item = $('#brz-acs-underline');
          item.addClass('brz-acs-active');
          item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
          if (docElement.hasClass('brz-acs-underline-style-0')) {
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (docElement.hasClass('brz-acs-underline-style-1')) {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (docElement.hasClass('brz-acs-underline-style-2')) {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
          }
      }

      // Font Size
      const currentFontSize = docElement.css('fontSize');
      if (currentFontSize && currentFontSize !== '') {
          const item = $('#brz-acs-font-size');
          // item.addClass('brz-acs-active');
          // item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
          if (currentFontSize === '1.3rem') {
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (currentFontSize === '1.5rem') {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (currentFontSize === '1.8rem') {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
          }
      }

      // Line Height
      if (docElement.hasClass('brz-acs-line-height-0') || docElement.hasClass('brz-acs-line-height-1') || docElement.hasClass('brz-acs-line-height-2')) {
          const item = $('#brz-acs-line-height');
          // item.addClass('brz-acs-active');
          // item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
          if (docElement.hasClass('brz-acs-line-height-0')) {
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (docElement.hasClass('brz-acs-line-height-1')) {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (docElement.hasClass('brz-acs-line-height-2')) {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
          }
      }

      // Letter Spacing
      const currentLetterSpacing = docElement.css('letterSpacing');
      if (currentLetterSpacing && currentLetterSpacing !== '') {
          const item = $('#brz-acs-letter-spacing');
          // item.addClass('brz-acs-active');
          // item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
          if (currentLetterSpacing === '0.1rem') {
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (currentLetterSpacing === '0.2rem') {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (currentLetterSpacing === '0.3rem') {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
          }
      }

      // Text Align
      const currentTextAlign = docElement.css('textAlign');
      if (currentTextAlign && currentTextAlign !== '') {
          const item = $('#brz-acs-text-align');
          // item.addClass('brz-acs-active');
          // item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
          if (currentTextAlign === 'left') {
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (currentTextAlign === 'center') {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (currentTextAlign === 'right') {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
          }
      }

      // Contrast
      if (docElement.hasClass('brz-acs-contrast-style-0') || docElement.hasClass('brz-acs-contrast-style-1') || docElement.hasClass('brz-acs-contrast-style-2')) {
          const item = $('#brz-acs-contrast');
          item.addClass('brz-acs-active');
          item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
          if (docElement.hasClass('brz-acs-contrast-style-0')) {
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (docElement.hasClass('brz-acs-contrast-style-1')) {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (docElement.hasClass('brz-acs-contrast-style-2')) {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
          }
      }

      // Cursor
      if (cursor.hasClass('brz-acs-cursor-0') || cursor.hasClass('brz-acs-cursor-1') || cursor.hasClass('brz-acs-cursor-2')) {
          const item = $('#brz-acs-change-cursor');
          const triangle = $('#brz-acs-triangle-cursor');
          if (triangle.length) {
              triangle.css('display', 'none');
          }
          item.addClass('brz-acs-active');
          item.find('.brz-acs-acc-progress-parent').removeClass('brz-acs-hidden');
          if (cursor.hasClass('brz-acs-cursor-0')) {
              item.find('.brz-acs-acc-progress-child-1').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (cursor.hasClass('brz-acs-cursor-1')) {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').addClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').removeClass('brz-acs-active');
          } else if (cursor.hasClass('brz-acs-cursor-2')) {
              item.find('.brz-acs-acc-progress-child-1').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-2').removeClass('brz-acs-active');
              item.find('.brz-acs-acc-progress-child-3').addClass('brz-acs-active');
              if (triangle.length) {
                  triangle.css('display', 'block');
              }
          }
      }

      // Update accordion icon colors based on active state
      $('.brz-acs-acc-item').each(function() {
          const $item = $(this);
          const $accChild = $item.find('.brz-acs-acc-child');
          $item.find('path').css('fill', $accChild.hasClass('brz-acs-active') ? 'rgb(var(--rgb-ninth-lighter))' : 'rgb(var(--rgb-first))');
      });
  }

  // Initialize
  // $(window).on('beforeunload', saveSettings);
  loadSavedSettings();
  positionActiveStatus();

  // Enhanced Dragging functionality
  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let modalStartX = 0;
  let modalStartY = 0;
  let dragTimeout = null;
  let isDragMode = false;
  let currentDragPosition = null;

  // Load saved position
  function loadSavedPosition() {
    const saved = localStorage.getItem('brz-acs-modal-position');
    const modal = $('#brz-acs-accessibility-modal');
    
    if (saved) {
        try {
            const position = JSON.parse(saved);
            
            if (position.mode === 'fixed') {
                // Fixed position mode
                modal.removeClass(allPositions.join(' ') + ' brz-acs-floating brz-acs-dragging');
                modal.addClass(position.class);
                modal.css({
                    top: '',
                    left: '',
                    right: '',
                    bottom: '',
                    transform: '',
                    inset: '',
                    zIndex: '999999999',
                });
            } else if (position.mode === 'floating') {
                // Floating mode
                modal.removeClass(allPositions.join(' ') + ' brz-acs-floating brz-acs-dragging');
                modal.css({
                    top: position.top + 'px',
                    left: position.left + 'px',
                    right: 'auto',
                    bottom: 'auto',
                    transform: 'none'
                });
                updateFloatingPositionClass();
            }
        } catch(e) {
            console.error('Error loading position:', e);
            modal.removeClass(allPositions.join(' ') + ' brz-acs-floating brz-acs-dragging');
            modal.addClass('brz-acs-bottom-left brz-acs-close');
        }
    } else {
      modal.removeClass(allPositions.join(' ') + ' brz-acs-floating brz-acs-dragging');
      modal.addClass('brz-acs-bottom-left brz-acs-close'); 
    }
  }
  // Save current position
  function saveCurrentPosition() {
    const modal = $('#brz-acs-accessibility-modal');
    const rect = modal[0].getBoundingClientRect();
    
    let positionData = {
        timestamp: new Date().getTime()
    };
    
    if (modal.hasClass('brz-acs-floating')) {
        positionData.mode = 'floating';
        positionData.top = Math.round(rect.top);
        positionData.left = Math.round(rect.left);
    } else {
        positionData.mode = 'fixed';
        positionData.class = allPositions.find(pos => modal.hasClass(pos)) || 'brz-acs-bottom-left';
    }
    
    localStorage.setItem('brz-acs-modal-position', JSON.stringify(positionData));
  }

  // Update floating position class based on screen position
  function updateFloatingPositionClass() {
    const modal = $('#brz-acs-accessibility-modal');
    if (!modal.hasClass('brz-acs-floating')) return;
    
    const rect = modal[0].getBoundingClientRect();
    const windowHeight = window.innerHeight;
    const windowWidth = window.innerWidth;
    
    // Remove all floating position classes
    modal.removeClass(allPositions.join(' '));
    
    // Define screen quadrants
    const isTop = rect.top < windowHeight / 3;
    const isBottom = rect.top > (windowHeight * 2) / 3;
    const isLeft = rect.left < windowWidth / 3;
    const isRight = rect.left > (windowWidth * 2) / 3;
    const isCenterVertical = !isTop && !isBottom;
    const isCenterHorizontal = !isLeft && !isRight;
    
    // RTL adjustment: swap left/right perception
    let effectiveLeft = isRTLMode ? isRight : isLeft;
    let effectiveRight = isRTLMode ? isLeft : isRight;

    // Determine position class
    if (isCenterVertical && isCenterHorizontal) {
      modal.addClass('brz-acs-top-left');
    } else if (isTop && effectiveLeft) {
      modal.addClass('brz-acs-top-right');
    } else if (isTop && effectiveRight) {
      modal.addClass('brz-acs-top-left');
    } else if (isBottom && effectiveLeft) {
      modal.addClass('brz-acs-bottom-right');
    } else if (isBottom && effectiveRight) {
      modal.addClass('brz-acs-bottom-left');
    } else if (isTop) {
      modal.addClass(isRTLMode ? 'brz-acs-top-left' : 'brz-acs-top-right');
    } else if (isBottom) {
      modal.addClass(isRTLMode ? 'brz-acs-bottom-left' : 'brz-acs-bottom-right');
    } else if (effectiveLeft) {
      modal.addClass('brz-acs-bottom-left');
    } else {
      modal.addClass('brz-acs-top-left');
    }
  }

  // RTL detection function
  function isRTL() {
    return $('html').attr('dir') === 'rtl' || $('body').attr('dir') === 'rtl' || 
          document.documentElement.dir === 'rtl' || 
          $('html').css('direction') === 'rtl';
  }
  let haveDragged = false;
  // Enhanced drag functions with RTL support
  function handleDragStart(e) {
    const modal = $('#brz-acs-accessibility-modal');
    // Detect RTL on drag start
    isRTLMode = isRTL();
    
    // Prevent default for touch events
    if (e.cancelable && (e.type === 'touchstart' || e.type === 'touchmove')) {
        e.preventDefault();
    }
    
    // Store initial positions
    const rect = modal[0].getBoundingClientRect();
    
    // Get initial coordinates
    if (e.type.includes('touch')) {
        dragStartX = e.touches[0].clientX;
        dragStartY = e.touches[0].clientY;
    } else {
        dragStartX = e.clientX;
        dragStartY = e.clientY;
    }
    
    // Store modal position in screen coordinates
    modalStartX = rect.left;
    modalStartY = rect.top;

    if (modal.hasClass('brz-acs-bottom-left')) {
      modalStartY += rect.height;
    }
    if (modal.hasClass('brz-acs-bottom-right')) {
      modalStartX += rect.width;
      modalStartY += rect.height;
    }
    if (modal.hasClass('brz-acs-top-right')) {
      modalStartX += rect.width;
    }
    
    // Store the offset between mouse and modal corner
    dragOffsetX = dragStartX - modalStartX;
    dragOffsetY = dragStartY - modalStartY;
    
    isDragging = false;
    currentDragPosition = null;
    haveDragged = false;

    // Clear any existing timeout
    clearTimeout(dragTimeout);
    
    // Set timeout to differentiate between click and drag
    dragTimeout = setTimeout(() => {
        isDragging = true;
        modal.addClass('brz-acs-dragging');
        
        // Add floating class only if not already in floating mode
        if (!modal.hasClass('brz-acs-floating')) {
            modal.addClass('brz-acs-floating');
        }        
    }, 500);

    // Add global event listeners with namespace
    $(document)
    .off('.brzDrag')
    .on('mousemove.brzDrag', handleDragMove)
    .on('touchmove.brzDrag', { passive: false }, handleDragMove)
    .on('mouseup.brzDrag', handleDragEnd)
    .on('touchend.brzDrag touchcancel.brzDrag', handleDragEnd)
    .on('mouseleave.brzDrag', handleDragEnd);
    
    return false;
  }

  // Handle drag movement with improved accuracy
  function handleDragMove(e) {
    if (!isDragging) return;
    
    const modal = $('#brz-acs-accessibility-modal');
    let clientX, clientY;
    
    // Get current coordinates
    if (e.type.includes('touch')) {
        if (!e.touches[0]) return;
        clientX = e.touches[0].clientX;
        clientY = e.touches[0].clientY;
        // Prevent default scrolling
        if (e.cancelable) e.preventDefault();
    } else {
        clientX = e.clientX;
        clientY = e.clientY;
    }
    
    // Calculate new position based on mouse offset
    let newX = clientX - dragOffsetX;
    let newY = clientY - dragOffsetY;
    haveDragged = true
    // Get modal dimensions based on current state
    let modalWidth, modalHeight;
    
    // Opened state - full modal dimensions
    modalWidth = modal.outerWidth();
    modalHeight = modal.outerHeight();
    
    // Ensure we have valid dimensions
    if (modalWidth === 0) modalWidth = 500; // Default max-width
    if (modalHeight === 0) modalHeight = Math.min(500, window.innerHeight * 0.7);
    
    // Constrain to viewport with safe margin
    const margin = 10;
    const maxX = window.innerWidth - modalWidth - margin;
    const maxY = window.innerHeight - modalHeight - margin;
    const minX = margin;
    const minY = margin;
    
    // Apply RTL adjustments if needed
    if (isRTLMode) {
        // For RTL, we need to consider the modal width differently
        // Constrain to ensure modal stays fully visible
        newX = Math.max(minX, Math.min(newX, maxX));
    } else {
        // Standard LTR constraint
        newX = Math.max(minX, Math.min(newX, maxX));
    }
    
    // Always constrain vertical position
    newY = Math.max(minY, Math.min(newY, maxY));
    
    if ($(".brz-acs-active").hasClass('brz-acs-active')) $(".brz-acs-active").removeClass("brz-acs-active");
    
    // Additional safety check for opened modal
    if (!modal.hasClass('brz-acs-close') && !modal.hasClass('brz-acs-floating')) {
        // For opened modal, ensure it doesn't cover important screen areas
        const viewportCenterY = window.innerHeight / 2;
        const modalCenterY = newY + (modalHeight / 2);
        
        // If modal is too high and might cover top navigation, adjust
        if (newY < 50) { // Too close to top
            newY = 50;
        }
        
        // If modal is too low and might cover bottom controls, adjust
        if (newY > window.innerHeight - modalHeight - 100) { // Too close to bottom
            newY = window.innerHeight - modalHeight - 100;
        }
    }
    
    // Apply new position with smooth update
    modal.css({
        top: newY + 'px',
        left: newX + 'px',
        right: 'auto',
        bottom: 'auto',
        transform: 'none',
        transition: 'none'
    });
    
    // Update position classes
    updateFloatingPositionClass();
    
    // Prevent text selection during drag
    if (e.cancelable) {
        e.preventDefault();
    }
    
    return false;
  }

  // Handle drag end with improved cleanup
  function handleDragEnd(e) {
    // Clear timeout
    clearTimeout(dragTimeout);
    dragTimeout = null;
    
    const modal = $('#brz-acs-accessibility-modal');
    
    // Remove event listeners first
    $(document).off('.brzDrag');
  
    // Save position immediately
    saveCurrentPosition();
    
    // Reset dragging state
    isDragging = false;
    dragOffsetX = 0;
    dragOffsetY = 0;
    
    modal.css('transition', 'all 0.1s ease');
    setTimeout(() => {
      modal.css('transition', '');
    }, 100);
    if (!haveDragged) {
      accessibilityModalOpenCloseToggle();
      haveDragged = false;
    }
    setTimeout(() => {
      modal.removeClass('brz-acs-dragging');
      modal.removeClass('brz-acs-floating');
    }, 5);
    
    if (e.type.includes('touch')) {
        e.preventDefault();
    }
    
    // Prevent click event from firing after drag
    e.stopPropagation();
    
    // Always reset RTL mode
    isRTLMode = false;
  }
  function initPositionHandlers() {
    // Update position button event handlers
    $(document).off("click", "[id^='brz-acs-align-']").on("click", "[id^='brz-acs-align-']", function() {
        const buttonId = $(this).attr('id');
        const positionMap = {
            'brz-acs-align-acc-top-left': 'brz-acs-top-left',
            'brz-acs-align-acc-top-right': 'brz-acs-top-right',
            'brz-acs-align-acc-bottom-left': 'brz-acs-bottom-left',
            'brz-acs-align-acc-bottom-right': 'brz-acs-bottom-right'
        };
        if (positionMap[buttonId]) {
            handlePositionChange(positionMap[buttonId]);
        }
    });
    
    // Initialize drag handlers
    const closeBtn = $('#brz-acs-closeBtn');
    closeBtn.off('mousedown.drag touchstart.drag');
    closeBtn.on('mousedown.drag', handleDragStart);
    closeBtn.on('touchstart.drag', { passive: false }, handleDragStart);
    
    // Window resize handler
    $(window).off('resize.brzPos').on('resize.brzPos', function() {
        updateFloatingPositionClass();
    });

    // Prevent text selection while dragging
    closeBtn.on('selectstart dragstart', function(e) {
      if (isDragging) {
          e.preventDefault();
          return false;
      }
    });
  }

  // Handle window resize
  $(window).off('resize.brzFloat').on('resize.brzFloat', function() {
      updateFloatingPositionClass();
  });

  loadSavedPosition();
  initPositionHandlers();
  positionActiveStatus();


  function handleWindowChange() {
    let modal = $("#brz-acs-accessibility-modal");
    let rect = modal[0].getBoundingClientRect();
    let outerWidth = window.innerWidth - (rect.x + rect.width + 15);
    let outerHeight = window.innerHeight - (rect.y + rect.height + 15);
    let xWidth = rect.x - 15;
    let yWidth = rect.y - 15;
    if (xWidth < 0) {
      modal.css({
        left: (rect.x - xWidth) + 'px',
      });
    }
    if (yWidth < 0) {
      modal.css({
        top: (rect.y - yWidth) + 'px',
      });
    }
    if (outerWidth < 0) {
      modal.css({
        left: (rect.x + outerWidth) + 'px',
      });
    }
    if (outerHeight < 0) {
      modal.css({
        top: (rect.y + outerHeight) + 'px'
      });
    }
  }

  const observer = new MutationObserver((mutations) => {
    mutations.forEach(mutation => {
        if (mutation.type == 'attributes') {
          handleWindowChange();
          setTimeout(() => handleWindowChange, 100)
          setTimeout(() => handleWindowChange, 300)
        }
    });
  });
  $(window).on("resize", handleWindowChange);
  observer.observe(document.getElementById("brz-acs-accessibility-modal"), { childList: false, subtree: false, attributes: true});
});

