import Head from 'next/head'
import { Inter } from 'next/font/google'
import styles from '@/styles/Home.module.css'
import Image from 'next/image'
import s from './index.module.scss'
import axios from "axios";
import { useState } from 'react';
import { generateDeviceId } from '@/utils/device'
import PhoneInput from 'react-phone-input-2';
import "react-phone-input-2/lib/bootstrap.css";


const inter = Inter({ subsets: ['latin'] })

export default function Home() {
	let [vonageid, setVonageid] = useState<string>("");

	async function verifyOTPVonage(otp: string) {
		console.log("client verify otp");
		console.log(otp, vonageid);
		console.log("------------------")
		let body = JSON.stringify({ "code": otp, "vonageRequestId": vonageid });
		let options = {
			url: "/api/otp/verify",
			method: "POST",
			headers: { 'Content-Type': 'application/json' },
			data: body,
		}

		let response = await axios.request(options)
		let token = response.data.token;
		let uid = response.data.uid;
		let refresh_token = response.data.refresh_token;
		let is_new_user = response.data.is_new_user;
		let token_type = response.data.token_type;

		console.log(response.data);

		if (localStorage.getItem("token") != null) {
			localStorage.removeItem("token");
			localStorage.removeItem("refresh_token");
			localStorage.removeItem("uid");
			localStorage.removeItem("is_new_user");
			localStorage.removeItem("token_type");
		}
		localStorage.setItem("token", token);
		localStorage.setItem("refresh_token", refresh_token);
		localStorage.setItem("uid", uid);
		localStorage.setItem("is_new_user", is_new_user);
		localStorage.setItem("token_type", token_type);
	}

	async function requestOTPVonage(number: string) {
		console.log("client request otp");
		console.log(number);
		console.log("------------------")

		let body = JSON.stringify({ "number": number })
		let options = {
			url: "/api/otp/send",
			method: "POST",
			headers: { 'Content-Type': 'application/json' },
			data: body,
		}

		let response = await axios.request(options)

		if (response.status == 200) {
			let rstatus = response.data.status;
			let rvonageid = response.data.vonageRequestId;
			console.log(response.data);
			setVonageid(rvonageid);
			setRequestedOtp(true);
		} else {
			console.log(response.data);
		}
	}

	let [inputNumber, setInputNumber] = useState<string>("");
	let [inputOTP, setInputOTP] = useState<string>("");
	let [requestedOtp, setRequestedOtp] = useState<boolean>(false);

	return (
		<div className={s.log}>
			{
				!requestedOtp ? 
				<div className={s.login}>
					<div className={s.text}>
						login using your phone number
					</div>

					<div className={s.number}>
						<PhoneInput
							placeholder={'xxxyyyzzzz'}
							enableSearch={true}
							country={'us'}
							value={inputNumber}
							onChange={phone => setInputNumber('+' + phone)}
							inputClass={s.digits}
							dropdownClass={s.dropdown}
							searchClass={s.search}
							buttonClass={s.button}
							containerClass={s.cont}
						/>
						<button className={s.send} onClick={() => requestOTPVonage(inputNumber)}>
							send
						</button>
					</div>
				</div> 
				:
				<div className={s.verify}>
					<div className={s.text}>
						enter the one time passcode
					</div>
					<div className={s.number}>
						<input className={`${s.digits} ${s.space}`} onChange={(event) => {setInputOTP(event.target.value);}} placeholder={'000111'}></input>
						<button className={s.send} onClick={() => verifyOTPVonage(inputOTP)}>
							send
						</button>
					</div>
				</div>
			}
		</div>
	)
}