import {
  AlertCircleIcon,
  AlertHexagonIcon,
  AlignBoxBottomLeftIcon,
  ApertureIcon,
  AppsIcon,
  AppWindowIcon,
  BasketIcon,
  BorderAllIcon,
  BorderHorizontalIcon,
  BorderInnerIcon,
  BorderStyle2Icon,
  BorderTopIcon,
  BorderVerticalIcon,
  BoxAlignBottomIcon,
  BoxAlignLeftIcon,
  BoxIcon,
  BoxModelIcon,
  BrandTidalIcon,
  CalendarIcon,
  CardboardsIcon,
  ChartArcsIcon,
  ChartAreaIcon,
  ChartCandleIcon,
  ChartDonut3Icon,
  ChartDotsIcon,
  ChartLineIcon,
  ChartRadarIcon,
  ColumnsIcon,
  CopyIcon,
  CurrencyDollarIcon,
  EditIcon,
  EyeTableIcon,
  FidgetSpinnerIcon,
  FileCheckIcon,
  FileDotsIcon,
  FilesIcon,
  FileTextIcon,
  FilterIcon,
  HelpIcon,
  JumpRopeIcon,
  LayoutDashboardIcon,
  LayoutKanbanIcon,
  LoginIcon,
  MailIcon,
  Message2Icon,
  MoodHappyIcon,
  PageBreakIcon,
  PhotoAiIcon,
  PlusIcon,
  PointIcon,
  RotateIcon,
  RowInsertBottomIcon,
  SearchIcon,
  ServerIcon,
  SettingsIcon,
  ShoppingCartIcon,
  SocialIcon,
  SortAscendingIcon,
  TableIcon,
  TicketIcon,
  TypographyIcon,
  UserCircleIcon,
  UserPlusIcon,
  UserShieldIcon,
  ZoomCodeIcon,
} from "vue-tabler-icons";
export interface menu {
  header?: string;
  title?: string;
  icon?: any;
  to?: string;
  chip?: string;
  chipColor?: string;
  chipVariant?: string;
  chipIcon?: string;
  children?: menu[];
  disabled?: boolean;
  type?: string;
  subCaption?: string;
  external?: boolean;
  userRoleRestrictions?: string[];
}

const sidebarItem: menu[] = [
  { header: "Home" },
  {
    title: "Dashboard",
    icon: LayoutDashboardIcon,
    to: "/",
    external: false,
  },
  {
    title: "Assignments",
    icon: FileTextIcon,
    to: "/assignments",
    external: false,
    children: [
      {
        title: "View All",
        icon: PointIcon,
        to: "/assignments",
        external: false,
      },
      {
        title: "Create Assignment",
        icon: PlusIcon,
        to: "/assignments/create",
        external: false,
        userRoleRestrictions: ["Teacher"],
      },
    ],
  },
];
export default sidebarItem;
