import UploadPage from "./UploadPage";
import { GLOBAL_STYLES } from "../utils/constants";

export default function Home() {

  return (
    <>
      <style>{GLOBAL_STYLES}</style>
      <UploadPage />
    </>
  );
}